import os
import sys
import json
import time
import base64
import hashlib
import requests
import socket
import random
import subprocess
import tempfile
import urllib.parse
import concurrent.futures
from datetime import datetime, timezone
from cryptography.fernet import Fernet

SOURCES_FILE = "sources.enc"
OUTPUT_FULL = "nodes_full.txt"
OUTPUT_FEATURED = "nodes_featured.txt"
OUTPUT_TOP100 = "nodes_top_100.txt"
REPORT_DIR = "report"

TIMEOUT = 15
MAX_RETRIES = 2
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
DOWNLOAD_WORKERS = 10
TARGET_FEATURED = 5000
TARGET_TOP100 = 100

_TAGS = [
    "Alpha Node", "Beta Cluster", "Gamma Pool", "Delta Group", "Epsilon Set",
    "Zeta Archive", "Eta Bundle", "Theta Mesh", "Iota Route", "Kappa Exit",
    "Lambda Relay", "Mu Uplink", "Nu Backbone", "Xi Access", "Omicron Proxy",
    "Pi Gateway", "Rho Bridge", "Sigma Link", "Tau Tunnel", "Upsilon Edge"
]

VALID_PREFIXES = ("vless://", "vmess://", "trojan://", "ss://", "socks5://", "hysteria2://", "hy2://")

def process_tag(index: int, url: str) -> str:
    h = hashlib.sha256(url.encode()).digest()
    base = _TAGS[h[0] % len(_TAGS)]
    return f"{base} {index}"

def classify_error(exc: Exception | None, status: int | None = None) -> str:
    if status is not None:
        return f"http_{status}"
    if exc is None:
        return "unknown"
    name = type(exc).__name__
    if "Timeout" in name: return "timeout"
    if "ConnectionError" in name or "Connect" in name: return "connection_failed"
    if "InvalidURL" in name or "MissingSchema" in name: return "invalid_url"
    return "request_failed"

def load_sources() -> list[str]:
    password = os.environ["SOURCES_KEY"].encode()
    key = base64.urlsafe_b64encode(hashlib.sha256(password).digest())
    cipher = Fernet(key)
    
    with open(SOURCES_FILE, "rb") as f:
        plaintext = cipher.decrypt(f.read()).decode("utf-8")

    sources = []
    seen = set()
    for line in plaintext.splitlines():
        line = line.strip()
        if not line or line.startswith("#"): continue
        if line.startswith("*"): line = line[1:].strip()
        if not line.startswith(("http://", "https://")): continue
        if line in seen: continue
        seen.add(line)
        sources.append(line)
    return sources

def download_source(url: str) -> tuple[list[str], bool, str]:
    last_err = "unknown"
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})
            if r.status_code == 200:
                configs = []
                for line in r.text.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"): continue
                    if any(line.startswith(p) for p in VALID_PREFIXES):
                        configs.append(line)
                return configs, True, ""
            last_err = classify_error(None, r.status_code)
        except Exception as e:
            last_err = classify_error(e)
        if attempt < MAX_RETRIES - 1: time.sleep(1.0)
    return [], False, last_err

def extract_host_port(config: str) -> tuple[str, int]:
    try:
        if "@" in config:
            netloc = config.split("@")[1].split("/")[0].split("?")[0].split("#")[0]
        else:
            match = urllib.parse.urlparse(config)
            if not match.hostname: return None, None
            return match.hostname, match.port
        if ":" in netloc:
            host, port = netloc.rsplit(":", 1)
            return host, int(port)
        return None, None
    except:
        return None, None

def test_tcp_latency(config: str) -> tuple[bool, float]:
    host, port = extract_host_port(config)
    if not host or not port: return False, 0.0
    try:
        start = time.time()
        with socket.create_connection((host, port), timeout=3):
            return True, round((time.time() - start) * 1000, 2)
    except:
        return False, 0.0

def benchmark_system() -> int:
    print("\nBenchmarking system & network speed...")
    start = time.time()
    try:
        requests.get("https://1.1.1.1", timeout=5)
        speed = round(time.time() - start, 3)
        if speed < 0.2: workers = 100
        elif speed < 0.5: workers = 50
        else: workers = 20
        print(f"  Network speed: {speed}s -> Using {workers} workers.")
        return workers
    except:
        print("  Network unstable. Falling back to 10 workers.")
        return 10

def test_xray_latency(config: str, xray_path: str) -> tuple[bool, float]:
    host, port = extract_host_port(config)
    if not host or not port: return False, 0.0
    
    temp_json = {
        "log": {"loglevel": "none"},
        "outbounds": [{"protocol": "freedom"}],
        "inbounds": [{"port": 10808, "protocol": "socks", "settings": {"auth": "noauth", "udp": False}}]
    }
    
    temp_cfg_path = None
    proc = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(temp_json, f)
            temp_cfg_path = f.name
            
        proc = subprocess.Popen([xray_path, "-c", temp_cfg_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.0)
        
        try:
            proxies = {"http": "socks5://127.0.0.1:10808", "https": "socks5://127.0.0.1:10808"}
            start = time.time()
            res = requests.get("https://api.ipify.org", proxies=proxies, timeout=4)
            if res.status_code == 200:
                return True, round((time.time() - start) * 1000, 2)
        except:
            pass
        return False, 0.0
    except Exception:
        return False, 0.0
    finally:
        if proc:
            proc.terminate()
            try: proc.wait(timeout=1)
            except: proc.kill()
        if temp_cfg_path and os.path.exists(temp_cfg_path):
            os.unlink(temp_cfg_path)

def collect_and_scan_full(sources: list[str], workers: int) -> tuple[list[dict], dict]:
    started_at = time.time()
    print("=" * 60)
    print(f"Qode — Full Collection ({len(sources)} sources, parallel)")
    print("=" * 60)

    all_configs = []
    seen = set()
    failed = []
    completed = 0
    raw_total = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as executor:
        futures = {executor.submit(download_source, url): (i, url) for i, url in enumerate(sources, 1)}
        for future in concurrent.futures.as_completed(futures):
            i, url = futures[future]
            configs, ok, err = future.result()
            completed += 1
            if ok:
                raw_total += len(configs)
                new = 0
                for c in configs:
                    if c not in seen:
                        seen.add(c)
                        all_configs.append(c)
                        new += 1
                print(f"[{completed:02d}/{len(sources):02d}] -> +{new} new (total: {len(all_configs)})")
            else:
                failed.append({"id": i, "tag": process_tag(i, url), "error": err})
                print(f"[{completed:02d}/{len(sources):02d}] -> {err}")

    print(f"\nScanning {len(all_configs)} proxies for TCP Liveness & Speed...")
    alive_tcp = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(test_tcp_latency, c): c for c in all_configs}
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            config = futures[future]
            ok, lat = future.result()
            if ok:
                alive_tcp.append({"config": config, "tcp_latency": lat})
            if (i+1) % 10000 == 0:
                print(f"  └─ Checked {i+1}/{len(all_configs)} | Alive: {len(alive_tcp)}")
                
    alive_tcp.sort(key=lambda x: x["tcp_latency"])
    print(f"Found {len(alive_tcp)} alive proxies. Sorted by TCP speed.")

    duration = round(time.time() - started_at, 2)
    report = {
        "label": "full",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": duration,
        "sources_total": len(sources),
        "sources_ok": len(sources) - len(failed),
        "sources_failed": len(failed),
        "raw_count": raw_total,
        "unique_count": len(all_configs),
        "alive_count": len(alive_tcp),
        "failed_sources": failed
    }
    return alive_tcp, report

def build_featured(alive_full: list[dict], workers: int, xray_exe: str) -> tuple[list[dict], dict]:
    print("\n" + "=" * 60)
    print(f"Qode — Featured Collection (Target: {TARGET_FEATURED} Xray-Alive)")
    print("=" * 60)
    
    featured = []
    index = 0
    started_at = time.time()
    
    while len(featured) < TARGET_FEATURED and index < len(alive_full):
        batch = alive_full[index:index + workers]
        index += workers
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(test_xray_latency, item["config"], xray_exe): item for item in batch}
            for future in concurrent.futures.as_completed(futures):
                item = futures[future]
                ok, lat = future.result()
                if ok:
                    featured.append({
                        "config": item["config"],
                        "tcp_latency": item["tcp_latency"],
                        "xray_latency": lat
                    })
                    if len(featured) >= TARGET_FEATURED:
                        break
                        
        print(f"  └─ Scanned up to index {index} | Xray-Alive: {len(featured)}/{TARGET_FEATURED}")

    featured.sort(key=lambda x: (x["xray_latency"], x["tcp_latency"]))
    
    report = {
        "label": "featured",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(time.time() - started_at, 2),
        "target_count": TARGET_FEATURED,
        "achieved_count": len(featured)
    }
    return featured, report

def build_top100(featured: list[dict], workers: int, xray_exe: str) -> tuple[list[dict], dict]:
    print("\n" + "=" * 60)
    print(f"Qode — TOP 100 Premium (Target: {TARGET_TOP100})")
    print("=" * 60)
    
    top_100 = []
    index = 0
    started_at = time.time()
    
    def deep_test(item):
        success = 0
        latencies = []
        for _ in range(3):
            ok_tcp, _ = test_tcp_latency(item["config"])
            if ok_tcp:
                ok_xray, lat = test_xray_latency(item["config"], xray_exe)
                if ok_xray:
                    success += 1
                    latencies.append(lat)
        if success == 3:
            return {"config": item["config"], "xray_latency": sum(latencies)/3}
        return None

    while len(top_100) < TARGET_TOP100 and index < len(featured):
        batch = featured[index:index + workers]
        index += workers
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(deep_test, item) for item in batch]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res:
                    top_100.append(res)
                    if len(top_100) >= TARGET_TOP100:
                        break
                        
        print(f"  └─ Deep tested up to index {index} | TOP: {len(top_100)}/{TARGET_TOP100}")

    top_100.sort(key=lambda x: x["xray_latency"])
    
    report = {
        "label": "top_100",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(time.time() - started_at, 2),
        "achieved_count": len(top_100)
    }
    return top_100, report

def main():
    os.makedirs(REPORT_DIR, exist_ok=True)
    workers = benchmark_system()
    sources = load_sources()
    
    xray_exe = os.path.join("xray-core", "xray.exe") if os.name == 'nt' else os.path.join("xray-core", "xray")
    if not os.path.exists(xray_exe):
        print("Xray executable not found! Exiting.")
        sys.exit(1)

    # 1. Full
    alive_full, full_report = collect_and_scan_full(sources, workers)
    with open(os.path.join(REPORT_DIR, "full.json"), "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2, ensure_ascii=False)
    with open(OUTPUT_FULL, "w", encoding="utf-8") as f:
        f.write("\n".join([x["config"] for x in alive_full]))
    print(f"→ {OUTPUT_FULL} saved.")

    # 2. Featured
    if alive_full:
        featured, featured_report = build_featured(alive_full, max(10, workers//2), xray_exe)
        with open(os.path.join(REPORT_DIR, "featured.json"), "w", encoding="utf-8") as f:
            json.dump(featured_report, f, indent=2, ensure_ascii=False)
        with open(OUTPUT_FEATURED, "w", encoding="utf-8") as f:
            f.write("\n".join([x["config"] for x in featured]))
        print(f"→ {OUTPUT_FEATURED} saved.")

        # 3. Top 100
        if featured:
            top_100, top100_report = build_top100(featured, max(5, workers//4), xray_exe)
            with open(os.path.join(REPORT_DIR, "top_100.json"), "w", encoding="utf-8") as f:
                json.dump(top100_report, f, indent=2, ensure_ascii=False)
            with open(OUTPUT_TOP100, "w", encoding="utf-8") as f:
                f.write("\n".join([x["config"] for x in top_100]))
            print(f"→ {OUTPUT_TOP100} saved.")

    print("\n" + "=" * 60)
    print("Done.")
    print("=" * 60)

if __name__ == "__main__":
    main()