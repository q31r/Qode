import os
import sys
import json
import time
import base64
import hashlib
import requests
import socket
import random
import urllib.parse
import concurrent.futures
from datetime import datetime, timezone
from cryptography.fernet import Fernet

SOURCES_FILE = "sources.enc"
OUTPUT_FULL = "nodes_full.txt"
OUTPUT_CURATED = "nodes_curated.txt"
REPORT_DIR = "report"

TIMEOUT = 15
MAX_RETRIES = 2
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
DOWNLOAD_WORKERS = 10
TCP_WORKERS = 100

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

    all_sources = []
    curated_sources = []
    seen = set()

    for line in plaintext.splitlines():
        line = line.strip()
        if not line or line.startswith("#"): continue
        
        is_curated = line.startswith("*")
        if is_curated: line = line[1:].strip()
        
        if not line.startswith(("http://", "https://")): continue
        if line in seen: continue
        seen.add(line)
        
        all_sources.append(line)
        if is_curated:
            curated_sources.append(line)
            
    return all_sources, curated_sources

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

def download_and_filter(sources: list[str], label: str, workers: int) -> tuple[list[dict], dict]:
    started_at = time.time()
    print("=" * 60)
    print(f"Qode — {label} Collection ({len(sources)} sources)")
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
        "label": label,
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

def main():
    os.makedirs(REPORT_DIR, exist_ok=True)
    workers = benchmark_system()
    all_sources, curated_sources = load_sources()

    # 1. Curated (Starred sources with TCP scan)
    if curated_sources:
        curated_alive, curated_report = download_and_filter(curated_sources, "curated", workers)
        with open(os.path.join(REPORT_DIR, "curated.json"), "w", encoding="utf-8") as f:
            json.dump(curated_report, f, indent=2, ensure_ascii=False)
        with open(OUTPUT_CURATED, "w", encoding="utf-8") as f:
            f.write("\n".join([x["config"] for x in curated_alive]))
        print(f"→ {OUTPUT_CURATED} saved.")

    # 2. Full (All sources with TCP scan)
    if all_sources:
        full_alive, full_report = download_and_filter(all_sources, "full", workers)
        with open(os.path.join(REPORT_DIR, "full.json"), "w", encoding="utf-8") as f:
            json.dump(full_report, f, indent=2, ensure_ascii=False)
        with open(OUTPUT_FULL, "w", encoding="utf-8") as f:
            f.write("\n".join([x["config"] for x in full_alive]))
        print(f"→ {OUTPUT_FULL} saved.")

    print("\n" + "=" * 60)
    print("Done.")
    print("=" * 60)

if __name__ == "__main__":
    main()