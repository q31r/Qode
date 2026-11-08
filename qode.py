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
OUTPUT_CURATED = "nodes_curated.txt"
REPORT_DIR = "report"

TIMEOUT = 15
MAX_RETRIES = 2
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
DOWNLOAD_WORKERS = 10
XRAY_WORKERS = 5

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

def load_sources() -> tuple[list[str], list[str]]:
    password = os.environ["SOURCES_KEY"].encode()
    key = base64.urlsafe_b64encode(hashlib.sha256(password).digest())
    cipher = Fernet(key)
    
    with open(SOURCES_FILE, "rb") as f:
        plaintext = cipher.decrypt(f.read()).decode("utf-8")

    featured = []
    regular = []
    seen = set()

    for line in plaintext.splitlines():
        line = line.strip()
        if not line or line.startswith("#"): continue
        
        is_featured = line.startswith("*")
        if is_featured: line = line[1:].strip()
        
        if not line.startswith(("http://", "https://")): continue
        if line in seen: continue
        seen.add(line)
        
        if is_featured:
            featured.append(line)
        else:
            regular.append(line)
            
    return regular, featured

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
    
    socks_port = random.randint(20000, 60000)
    
    temp_json = {
        "log": {"loglevel": "none"},
        "outbounds": [{"protocol": "freedom"}],
        "inbounds": [{"port": socks_port, "protocol": "socks", "settings": {"auth": "noauth", "udp": False}}]
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
            proxies = {"http": f"socks5h://127.0.0.1:{socks_port}", "https": f"socks5h://127.0.0.1:{socks_port}"}
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

def download_curated(sources: list[str]) -> list[str]:
    print("\n" + "=" * 60)
    print(f"Qode — Curated Collection ({len(sources)} sources, no testing)")
    print("=" * 60)
    
    all_configs = []
    seen = set()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as executor:
        futures = {executor.submit(download_source, url): url for url in sources}
        for future in concurrent.futures.as_completed(futures):
            configs, ok, err = future.result()
            if ok:
                new = 0
                for c in configs:
                    if c not in seen:
                        seen.add(c)
                        all_configs.append(c)
                        new += 1
                print(f"  -> +{new} new (total: {len(all_configs)})")
            else:
                print(f"  -> {err}")

    return all_configs

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
    print("Qode — Featured Collection (Scanning all TCP-Alive)")
    print("=" * 60)
    
    featured = []
    started_at = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(test_xray_latency, item["config"], xray_exe): item for item in alive_full}
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            item = futures[future]
            ok, lat = future.result()
            if ok:
                featured.append({
                    "config": item["config"],
                    "tcp_latency": item["tcp_latency"],
                    "xray_latency": lat
                })
                
            if (i+1) % 1000 == 0:
                print(f"  └─ Scanned {i+1}/{len(alive_full)} | Xray-Alive: {len(featured)}")

    featured.sort(key=lambda x: (x["xray_latency"], x["tcp_latency"]))
    
    report = {
        "label": "featured",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(time.time() - started_at, 2),
        "total_scanned": len(alive_full),
        "achieved_count": len(featured)
    }
    return featured, report

def main():
    os.makedirs(REPORT_DIR, exist_ok=True)
    workers = benchmark_system()
    regular_sources, curated_sources = load_sources()
    
    xray_exe = os.path.join("xray-core", "xray.exe") if os.name == 'nt' else os.path.join("xray-core", "xray")
    if not os.path.exists(xray_exe):
        print("Xray executable not found! Exiting.")
        sys.exit(1)

    # 1. Curated (Starred sources, no testing)
    if curated_sources:
        curated_configs = download_curated(curated_sources)
        with open(OUTPUT_CURATED, "w", encoding="utf-8") as f:
            f.write("\n".join(curated_configs))
        print(f"→ {OUTPUT_CURATED} saved.")

    # 2. Full & Featured (Regular sources)
    alive_full, full_report = collect_and_scan_full(regular_sources, workers)
    with open(os.path.join(REPORT_DIR, "full.json"), "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2, ensure_ascii=False)
    with open(OUTPUT_FULL, "w", encoding="utf-8") as f:
        f.write("\n".join([x["config"] for x in alive_full]))
    print(f"→ {OUTPUT_FULL} saved.")

    if alive_full:
        featured, featured_report = build_featured(alive_full, XRAY_WORKERS, xray_exe)
        with open(os.path.join(REPORT_DIR, "featured.json"), "w", encoding="utf-8") as f:
            json.dump(featured_report, f, indent=2, ensure_ascii=False)
        with open(OUTPUT_FEATURED, "w", encoding="utf-8") as f:
            f.write("\n".join([x["config"] for x in featured]))
        print(f"→ {OUTPUT_FEATURED} saved.")

    print("\n" + "=" * 60)
    print("Done.")
    print("=" * 60)

if __name__ == "__main__":
    main()