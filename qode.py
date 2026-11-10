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
import geoip2.database
from datetime import datetime, timezone
from cryptography.fernet import Fernet
from collections import defaultdict

SOURCES_FILE = "sources.enc"
OUTPUT_FULL = "nodes_full.txt"
OUTPUT_CURATED = "nodes_curated.txt"
OUTPUT_FULL_B64 = "nodes_full_Base64.txt"
OUTPUT_CURATED_B64 = "nodes_curated_Base64.txt"
STATS_FILE = "stats.json"
REPORT_DIR = "report"
GEOIP_DB = "GeoLite2-Country.mmdb"

TIMEOUT = 8
TCP_RETRIES = 2
MAX_RETRIES = 2
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
DOWNLOAD_WORKERS = 10

PRIORITY_PORTS = {443, 8443, 2053, 2087, 2096, 2083, 8080, 8880, 2052, 2082}

_TAGS = [
    "Alpha Node", "Beta Cluster", "Gamma Pool", "Delta Group", "Epsilon Set",
    "Zeta Archive", "Eta Bundle", "Theta Mesh", "Iota Route", "Kappa Exit",
    "Lambda Relay", "Mu Uplink", "Nu Backbone", "Xi Access", "Omicron Proxy",
    "Pi Gateway", "Rho Bridge", "Sigma Link", "Tau Tunnel", "Upsilon Edge"
]

VALID_PREFIXES = ("vless://", "vmess://", "trojan://", "ss://", "socks5://", "hysteria2://", "hy2://")

VALID_SS_METHODS = {
    "aes-256-gcm", "aes-128-gcm", "chacha20-ietf-poly1305", "aes-256-cfb",
    "aes-128-cfb", "chacha20", "xchacha20-ietf-poly1305",
    "2022-blake3-aes-128-gcm", "2022-blake3-aes-256-gcm", "none"
}

def country_code_to_flag(code: str) -> str:
    if not code or len(code) != 2:
        return ""
    try:
        return "".join(chr(127397 + ord(c.upper())) for c in code)
    except:
        return ""

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

def validate_strict(config: str) -> bool:
    if not config or len(config) < 10:
        return False
    
    if config.startswith("vless://"):
        try:
            body = config[8:]
            if "@" not in body: return False
            userinfo, rest = body.split("@", 1)
            if not userinfo: return False
            host_port = rest.split("?")[0].split("#")[0].split("/")[0]
            parts = host_port.split(":")
            if len(parts) != 2: return False
            host, port_str = parts
            if not host or not port_str: return False
            port_num = int(port_str)
            if not (1 <= port_num <= 65535): return False
            return True
        except:
            return False
    
    if config.startswith("trojan://"):
        try:
            body = config[9:]
            if "@" not in body: return False
            password, rest = body.split("@", 1)
            if not password: return False
            host_port = rest.split("?")[0].split("#")[0].split("/")[0]
            parts = host_port.split(":")
            if len(parts) != 2: return False
            host, port_str = parts
            if not host or not port_str: return False
            port_num = int(port_str)
            if not (1 <= port_num <= 65535): return False
            return True
        except:
            return False
    
    if config.startswith("vmess://"):
        try:
            body = config[8:].split("#")[0].strip()
            padding = "=" * (-len(body) % 4)
            decoded = base64.b64decode(body + padding).decode("utf-8")
            data = json.loads(decoded)
            for field in ["v", "add", "port", "id"]:
                if field not in data: return False
            if not data.get("add"): return False
            if not data.get("id"): return False
            port_num = int(data.get("port", 0))
            if not (1 <= port_num <= 65535): return False
            return True
        except:
            return False
    
    if config.startswith("ss://"):
        try:
            body = config[5:].split("#")[0].split("?")[0]
            if "@" not in body: return False
            encoded_part, server_part = body.split("@", 1)
            padding = "=" * (-len(encoded_part) % 4)
            decoded = base64.b64decode(encoded_part + padding).decode("utf-8")
            if ":" not in decoded: return False
            method, password = decoded.split(":", 1)
            if not method or not password: return False
            if method not in VALID_SS_METHODS: return False
            host_port = server_part.split("/")[0]
            parts = host_port.split(":")
            if len(parts) != 2: return False
            host, port_str = parts
            if not host or not port_str: return False
            port_num = int(port_str)
            if not (1 <= port_num <= 65535): return False
            return True
        except:
            return False
    
    if config.startswith("socks5://"):
        try:
            body = config[9:]
            if "@" in body:
                auth, rest = body.split("@", 1)
                if ":" not in auth: return False
                user, passwd = auth.split(":", 1)
                if not user: return False
            else:
                rest = body
            host_port = rest.split("/")[0].split("?")[0].split("#")[0]
            parts = host_port.split(":")
            if len(parts) != 2: return False
            host, port_str = parts
            if not host or not port_str: return False
            port_num = int(port_str)
            if not (1 <= port_num <= 65535): return False
            return True
        except:
            return False
    
    if config.startswith("hysteria2://") or config.startswith("hy2://"):
        try:
            if config.startswith("hysteria2://"):
                body = config[12:]
            else:
                body = config[6:]
            if "@" not in body: return False
            password, rest = body.split("@", 1)
            if not password: return False
            host_port = rest.split("/")[0].split("?")[0].split("#")[0]
            parts = host_port.split(":")
            if len(parts) != 2: return False
            host, port_str = parts
            if not host or not port_str: return False
            port_num = int(port_str)
            if not (1 <= port_num <= 65535): return False
            return True
        except:
            return False
    
    return False

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
        if config.startswith("vmess://"):
            try:
                body = config[8:].split("#")[0].strip()
                padding = "=" * (-len(body) % 4)
                decoded = base64.b64decode(body + padding).decode("utf-8")
                data = json.loads(decoded)
                host = data.get("add")
                port = data.get("port")
                if host and port:
                    return str(host), int(port)
            except:
                pass
        
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

def extract_identity(config: str) -> str | None:
    try:
        if config.startswith("vless://"):
            return config.replace("vless://", "").split("@")[0]
        if config.startswith("trojan://"):
            return config.replace("trojan://", "").split("@")[0]
        if config.startswith("hysteria2://"):
            return config.replace("hysteria2://", "").split("@")[0]
        if config.startswith("hy2://"):
            return config.replace("hy2://", "").split("@")[0]
        if config.startswith("socks5://"):
            body = config.replace("socks5://", "")
            if "@" in body: return body.split("@")[0]
            return None
        if config.startswith("ss://"):
            body = config.replace("ss://", "").split("#")[0].split("?")[0]
            if "@" in body: return body.split("@")[0]
            try:
                decoded = base64.b64decode(body + "===").decode("utf-8", errors="ignore")
                if "@" in decoded: return decoded.split("@")[0]
            except: pass
            return None
        if config.startswith("vmess://"):
            try:
                body = config.replace("vmess://", "").split("#")[0]
                decoded = base64.b64decode(body + "===").decode("utf-8", errors="ignore")
                data = json.loads(decoded)
                return data.get("id")
            except: return None
    except: return None
    return None

def deduplicate_configs(configs: list[str]) -> list[str]:
    seen_keys = set()
    result = []
    for config in configs:
        host, port = extract_host_port(config)
        identity = extract_identity(config)
        protocol = config.split("://")[0] if "://" in config else "unknown"
        if host and port and identity:
            key = (protocol, host, port, identity)
        else:
            key = None
        if key is None:
            result.append(config)
            continue
        if key in seen_keys:
            continue
        seen_keys.add(key)
        result.append(config)
    return result

def test_tcp_latency(config: str) -> tuple[bool, float]:
    host, port = extract_host_port(config)
    if not host or not port: return False, 0.0
    
    best_latency = None
    for attempt in range(TCP_RETRIES):
        try:
            start = time.time()
            with socket.create_connection((host, port), timeout=TIMEOUT):
                latency = round((time.time() - start) * 1000, 2)
                if best_latency is None or latency < best_latency:
                    best_latency = latency
                return True, best_latency
        except:
            if attempt < TCP_RETRIES - 1:
                time.sleep(0.5)
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

def build_display_name(host: str, reader) -> str:
    country_name = None
    country_code = None
    resolved_ip = None
    
    if host:
        try:
            socket.inet_aton(host)
            resolved_ip = host
        except (socket.error, OSError):
            try:
                resolved_ip = socket.gethostbyname(host)
            except:
                resolved_ip = None
        
        if resolved_ip and reader:
            try:
                response = reader.country(resolved_ip)
                country_name = response.country.name
                country_code = response.country.iso_code
            except:
                pass
    
    parts = []
    if country_name and country_code:
        flag = country_code_to_flag(country_code)
        if flag:
            parts.append(f"{flag} {country_name}")
        else:
            parts.append(country_name)
    elif country_name:
        parts.append(country_name)
    
    if resolved_ip:
        parts.append(resolved_ip)
    elif host:
        parts.append(host)
    
    parts.append("By q31r")
    return " - ".join(parts)

def rewrite_display_names(configs: list[str], label: str) -> list[str]:
    reader = None
    if os.path.exists(GEOIP_DB):
        try:
            reader = geoip2.database.Reader(GEOIP_DB)
            print(f"\n  🌍 Rewriting display names for {len(configs)} configs...")
        except Exception as e:
            print(f"  ⚠️  GeoIP database error: {e}")
    else:
        print(f"  ⚠️  GeoIP database '{GEOIP_DB}' not found. Using fallback names.")
    
    rewritten = []
    country_stats = defaultdict(int)
    no_country = 0
    
    for config in configs:
        try:
            host, _ = extract_host_port(config)
            if reader:
                display_name = build_display_name(host, reader)
            else:
                display_name = f"{host} - By q31r" if host else "By q31r"
            
            if " - " in display_name and display_name.split(" - ")[0]:
                first_part = display_name.split(" - ")[0]
                if any(ord(c) > 127000 for c in first_part):
                    country_stats[first_part] += 1
                else:
                    no_country += 1
            else:
                no_country += 1
            
            encoded_name = urllib.parse.quote(display_name, safe='')
            if "#" in config:
                new_config = config.split("#")[0] + "#" + encoded_name
            else:
                new_config = config + "#" + encoded_name
            rewritten.append(new_config)
        except Exception:
            rewritten.append(config)
            no_country += 1
    
    if reader:
        reader.close()
    
    print(f"  ✅ Rewritten: {len(rewritten)} | With country: {sum(country_stats.values())} | Without country: {no_country}")
    if country_stats:
        print(f"  📊 Top countries:")
        for country, count in sorted(country_stats.items(), key=lambda x: -x[1])[:5]:
            print(f"     {country}: {count}")
    
    return rewritten

def save_base64(configs: list[str], output_file: str):
    content = "\n".join(configs)
    encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(encoded)
    print(f"→ {output_file} saved (Base64).")

def download_and_filter(sources: list[str], label: str, workers: int) -> tuple[list[dict], dict]:
    started_at = time.time()
    print("=" * 60)
    print(f"Qode — {label} Collection ({len(sources)} sources)")
    print("=" * 60)

    all_configs = []
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
                all_configs.extend(configs)
                print(f"[{completed:02d}/{len(sources):02d}] -> +{len(configs)} new (raw total: {len(all_configs)})")
            else:
                failed.append({"id": i, "tag": process_tag(i, url), "error": err})
                print(f"[{completed:02d}/{len(sources):02d}] -> {err}")

    print(f"\n🔍 Filtering invalid configs with strict validation...")
    before_filter = len(all_configs)
    all_configs = [c for c in all_configs if validate_strict(c)]
    filtered_out = before_filter - len(all_configs)
    print(f"  Removed {filtered_out} invalid configs. Remaining: {len(all_configs)}")

    print(f"\n🧹 Deduplicating with precise keys...")
    before_dedup = len(all_configs)
    all_configs = deduplicate_configs(all_configs)
    dedup_removed = before_dedup - len(all_configs)
    print(f"  Removed {dedup_removed} duplicates. Remaining: {len(all_configs)}")

    print(f"\nScanning {len(all_configs)} proxies for TCP Liveness & Speed (timeout: {TIMEOUT}s, retries: {TCP_RETRIES})...")
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

    if alive_tcp:
        rewritten = rewrite_display_names([x["config"] for x in alive_tcp], label)
        for i, x in enumerate(alive_tcp):
            x["config"] = rewritten[i]

        for x in alive_tcp:
            _, port = extract_host_port(x["config"])
            x["priority"] = 1 if port in PRIORITY_PORTS else 0
        
        alive_tcp.sort(key=lambda x: (-x["priority"], x["tcp_latency"]))
        print(f"Re-sorted with priority ports at the top.")

    duration = round(time.time() - started_at, 2)
    report = {
        "label": label,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": duration,
        "sources_total": len(sources),
        "sources_ok": len(sources) - len(failed),
        "sources_failed": len(failed),
        "raw_count": raw_total,
        "filtered_out_invalid": filtered_out,
        "deduplicated_count": len(all_configs),
        "duplicates_removed": dedup_removed,
        "alive_count": len(alive_tcp),
        "failed_sources": failed
    }
    return alive_tcp, report

def main():
    os.makedirs(REPORT_DIR, exist_ok=True)
    workers = benchmark_system()
    all_sources, curated_sources = load_sources()

    stats = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "curated": {"total": 0, "alive": 0},
        "full": {"total": 0, "alive": 0},
        "sources": {"total": len(all_sources), "successful": 0, "failed": 0}
    }

    if curated_sources:
        curated_alive, curated_report = download_and_filter(curated_sources, "curated", workers)
        with open(os.path.join(REPORT_DIR, "curated.json"), "w", encoding="utf-8") as f:
            json.dump(curated_report, f, indent=2, ensure_ascii=False)
        
        curated_configs = [x["config"] for x in curated_alive]
        with open(OUTPUT_CURATED, "w", encoding="utf-8") as f:
            f.write("\n".join(curated_configs))
        print(f"→ {OUTPUT_CURATED} saved.")
        
        save_base64(curated_configs, OUTPUT_CURATED_B64)
        
        stats["curated"]["total"] = curated_report["deduplicated_count"]
        stats["curated"]["alive"] = curated_report["alive_count"]

    if all_sources:
        full_alive, full_report = download_and_filter(all_sources, "full", workers)
        with open(os.path.join(REPORT_DIR, "full.json"), "w", encoding="utf-8") as f:
            json.dump(full_report, f, indent=2, ensure_ascii=False)
        
        full_configs = [x["config"] for x in full_alive]
        with open(OUTPUT_FULL, "w", encoding="utf-8") as f:
            f.write("\n".join(full_configs))
        print(f"→ {OUTPUT_FULL} saved.")
        
        save_base64(full_configs, OUTPUT_FULL_B64)
        
        stats["full"]["total"] = full_report["deduplicated_count"]
        stats["full"]["alive"] = full_report["alive_count"]
        stats["sources"]["successful"] = full_report["sources_ok"]
        stats["sources"]["failed"] = full_report["sources_failed"]

    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"→ {STATS_FILE} saved.")

    print("\n" + "=" * 60)
    print("Done.")
    print("=" * 60)

if __name__ == "__main__":
    main()