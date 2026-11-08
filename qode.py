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
OUTPUT_10K = "nodes_10k.txt"
OUTPUT_5K = "nodes_5k.txt"
OUTPUT_FEATURED = "nodes_featured.txt"
REPORT_DIR = "report"

TIMEOUT = 15
MAX_RETRIES = 2
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
DOWNLOAD_WORKERS = 10

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
    full = []
    seen = set()

    for line in plaintext.splitlines():
        line = line.strip()
        if not line or line.startswith("#"): continue

        is_featured = line.startswith("*")
        if is_featured: line = line[1:].strip()

        if not line.startswith(("http://", "https://")): continue
        if line in seen: continue
        seen.add(line)

        full.append(line)
        if is_featured:
            featured.append(line)

    return featured, full

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

def sort_configs_by_protocol(configs: list[str]) -> list[str]:
    sorted_list = []
    for p in VALID_PREFIXES:
        protos = [c for c in configs if c.startswith(p)]
        sorted_list.extend(protos)
    return sorted_list

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

def test_tcp(config: str) -> bool:
    host, port = extract_host_port(config)
    if not host or not port: return False
    try:
        with socket.create_connection((host, port), timeout=5):
            return True
    except:
        return False

def benchmark_system() -> int:
    print("\nBenchmarking system & network speed...")
    start = time.time()
    try:
        requests.get("https://1.1.1.1", timeout=5)
        speed = round(time.time() - start, 3)
        if speed < 0.2:
            workers = 100
            print("  Ultra-fast network detected. Using 100 workers.")
        elif speed < 0.5:
            workers = 50
            print("  Fast network detected. Using 50 workers.")
        else:
            workers = 20
            print("  Moderate network. Using 20 workers.")
        return workers
    except:
        print("  Network unstable. Falling back to 10 workers.")
        return 10

def test_xray(config: str, xray_path: str) -> bool:
    host, port = extract_host_port(config)
    if not host or not port: return False
    
    temp_json = {
        "log": {"loglevel": "none"},
        "outbounds": [{"protocol": "freedom"}],
        "inbounds": [{
            "port": 10808,
            "protocol": "socks",
            "settings": {"auth": "noauth", "udp": False}
        }]
    }
    
    temp_cfg_path = None
    proc = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(temp_json, f)
            temp_cfg_path = f.name
            
        proc = subprocess.Popen([xray_path, "-c", temp_cfg_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.5)
        
        success = False
        try:
            proxies = {"http": "socks5://127.0.0.1:10808", "https": "socks5://127.0.0.1:10808"}
            res = requests.get("https://api.ipify.org", proxies=proxies, timeout=5)
            if res.status_code == 200:
                success = True
        except:
            pass
            
        return success
    except Exception:
        return False
    finally:
        if proc:
            proc.terminate()
            try: proc.wait(timeout=2)
            except: proc.kill()
        if temp_cfg_path and os.path.exists(temp_cfg_path):
            os.unlink(temp_cfg_path)

def collect_batch(sources: list[str], label: str) -> tuple[list[str], dict]:
    started_at = time.time()
    started_iso = datetime.now(timezone.utc).isoformat()

    print("=" * 60)
    print(f"Qode — {label} Collection ({len(sources)} sources, parallel)")
    print("=" * 60)

    all_configs = []
    seen = set()
    failed = []
    succeeded = 0
    raw_total = 0
    completed = 0

    results_map = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as executor:
        futures = {executor.submit(download_source, url): (i, url) for i, url in enumerate(sources, 1)}
        
        for future in concurrent.futures.as_completed(futures):
            i, url = futures[future]
            name = process_tag(i, url)
            configs, ok, err = future.result()
            completed += 1
            
            results_map[i] = (configs, name, err)
            
            if ok:
                new = 0
                for c in configs:
                    if c not in seen:
                        seen.add(c)
                        all_configs.append(c)
                        new += 1
                raw_total += len(configs)
                succeeded += 1
                print(f"[{completed:02d}/{len(sources):02d}] {name} -> +{new} new (total: {len(all_configs)})")
            else:
                failed.append({"id": i, "tag": name, "error": err})
                print(f"[{completed:02d}/{len(sources):02d}] {name} -> {err}")

    proto_counts = {}
    for c in all_configs:
        for p in VALID_PREFIXES:
            if c.startswith(p):
                proto_counts[p] = proto_counts.get(p, 0) + 1
                break

    duration = round(time.time() - started_at, 2)
    report = {
        "label": label,
        "timestamp": started_iso,
        "duration_seconds": duration,
        "sources_total": len(sources),
        "sources_ok": succeeded,
        "sources_failed": len(failed),
        "raw_count": raw_total,
        "unique_count": len(all_configs),
        "failed_sources": failed,
        "protocol_breakdown": proto_counts,
    }
    return all_configs, report

def scan_batch(configs: list[str], workers: int, target_count: int, test_func, test_name: str) -> list[str]:
    print(f"\nScanning {len(configs)} proxies for {test_name}...")
    alive = []
    
    random.shuffle(configs)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(test_func, c): c for c in configs}
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            config = futures[future]
            if future.result():
                alive.append(config)
            if (i+1) % 1000 == 0:
                print(f"  └─ Checked {i+1}/{len(configs)} | Alive: {len(alive)}")
            if target_count > 0 and len(alive) >= target_count:
                for f in futures: f.cancel()
                break
                
    print(f"Found {len(alive)} alive proxies after {test_name}.")
    return alive

def main():
    os.makedirs(REPORT_DIR, exist_ok=True)
    workers = benchmark_system()
    
    featured_sources, full_sources = load_sources()
    print(f"Loaded {len(featured_sources)} featured sources, {len(full_sources)} total sources.\n")

    full_configs, full_report = collect_batch(full_sources, "full")
    with open(os.path.join(REPORT_DIR, "full.json"), "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2, ensure_ascii=False)
        
    alive_full = []
    if len(full_configs) > 0:
        alive_full = scan_batch(full_configs, workers, 0, test_tcp, "TCP Liveness")
        alive_full_sorted = sort_configs_by_protocol(alive_full)
        with open(OUTPUT_FULL, "w", encoding="utf-8") as f:
            f.write("\n".join(alive_full_sorted))
        print(f"→ {OUTPUT_FULL} ({len(alive_full_sorted)} alive configs)")

    if len(alive_full) > 0:
        random.shuffle(alive_full)
        alive_10k = alive_full[:10000]
        alive_10k_sorted = sort_configs_by_protocol(alive_10k)
        with open(OUTPUT_10K, "w", encoding="utf-8") as f:
            f.write("\n".join(alive_10k_sorted))
        print(f"→ {OUTPUT_10K} ({len(alive_10k_sorted)} configs)")

        random.shuffle(alive_10k)
        alive_5k = alive_10k[:5000]
        alive_5k_sorted = sort_configs_by_protocol(alive_5k)
        with open(OUTPUT_5K, "w", encoding="utf-8") as f:
            f.write("\n".join(alive_5k_sorted))
        print(f"→ {OUTPUT_5K} ({len(alive_5k_sorted)} configs)")

    if len(featured_sources) > 0:
        featured_configs, featured_report = collect_batch(featured_sources, "featured")
        with open(os.path.join(REPORT_DIR, "featured.json"), "w", encoding="utf-8") as f:
            json.dump(featured_report, f, indent=2, ensure_ascii=False)
            
        if len(featured_configs) > 0:
            xray_exe = os.path.join("xray-core", "xray.exe") if os.name == 'nt' else os.path.join("xray-core", "xray")
            
            if os.path.exists(xray_exe):
                alive_featured = scan_batch(featured_configs, workers, 0, test_tcp, "TCP Liveness")
                if len(alive_featured) > 0:
                    premium = scan_batch(alive_featured, max(1, workers//2), 2000, lambda c: test_xray(c, xray_exe), "Xray Health")
                    premium_sorted = sort_configs_by_protocol(premium)
                    with open(OUTPUT_FEATURED, "w", encoding="utf-8") as f:
                        f.write("\n".join(premium_sorted))
                    print(f"→ {OUTPUT_FEATURED} ({len(premium_sorted)} premium configs)")
            else:
                print("Xray executable not found! Cannot process featured list.")

    print("\n" + "=" * 60)
    print("Done.")
    print("=" * 60)

if __name__ == "__main__":
    main()