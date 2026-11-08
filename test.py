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
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

SOURCES_FILE = "sources.enc"
TEST_DIR = "test"
os.makedirs(TEST_DIR, exist_ok=True)

TIMEOUT = 15
MAX_RETRIES = 2
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
XRAY_WORKERS = 5
TARGET_SERVERS = 500

VALID_PREFIXES = ("vless://", "vmess://", "trojan://", "ss://", "socks5://", "hysteria2://", "hy2://")

def load_sources() -> list[str]:
    print("Decrypting sources...")
    password = os.environ.get("SOURCES_KEY")
    if not password:
        print("Error: SOURCES_KEY not found in .env")
        sys.exit(1)
        
    key = base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())
    cipher = Fernet(key)
    
    try:
        with open(SOURCES_FILE, "rb") as f:
            plaintext = cipher.decrypt(f.read()).decode("utf-8")
    except Exception as e:
        print(f"Failed to decrypt: {e}")
        sys.exit(1)

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
            last_err = f"HTTP {r.status_code}"
        except Exception as e:
            last_err = type(e).__name__
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

def test_xray_latency(config: str, xray_path: str) -> tuple[bool, float, str]:
    host, port = extract_host_port(config)
    if not host or not port: return False, 0.0, "invalid_config"
    
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
            proxies = {"http": f"socks5://127.0.0.1:{socks_port}", "https": f"socks5://127.0.0.1:{socks_port}"}
            start = time.time()
            res = requests.get("https://api.ipify.org", proxies=proxies, timeout=4)
            if res.status_code == 200:
                return True, round((time.time() - start) * 1000, 2), "success"
        except Exception as e:
            return False, 0.0, type(e).__name__
        return False, 0.0, "unknown_failure"
    except Exception as e:
        return False, 0.0, f"xray_error: {type(e).__name__}"
    finally:
        if proc:
            proc.terminate()
            try: proc.wait(timeout=1)
            except: proc.kill()
        if temp_cfg_path and os.path.exists(temp_cfg_path):
            os.unlink(temp_cfg_path)

def main():
    print("=" * 60)
    print("🧪 Qode Xray Debug Test")
    print("=" * 60)
    
    xray_exe = os.path.join("xray-core", "xray.exe") if os.name == 'nt' else os.path.join("xray-core", "xray")
    if not os.path.exists(xray_exe):
        print("Xray executable not found!")
        sys.exit(1)
        
    sources = load_sources()
    random.shuffle(sources)
    
    all_configs = []
    seen = set()
    
    print(f"Downloading from random sources until we get {TARGET_SERVERS} proxies...")
    for url in sources:
        if len(all_configs) >= TARGET_SERVERS:
            break
            
        configs, ok, err = download_source(url)
        if ok:
            new = 0
            for c in configs:
                if c not in seen:
                    seen.add(c)
                    all_configs.append(c)
                    new += 1
                    if len(all_configs) >= TARGET_SERVERS:
                        break
            print(f"  Downloaded +{new} from a source (Total: {len(all_configs)})")
            
    print(f"\nCollected {len(all_configs)} unique configs.\n")
    
    print("Testing TCP...")
    tcp_alive = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(test_tcp_latency, c): c for c in all_configs}
        for future in concurrent.futures.as_completed(futures):
            config = futures[future]
            ok, _ = future.result()
            if ok:
                tcp_alive.append(config)
    
    print(f"TCP Alive: {len(tcp_alive)}/{len(all_configs)}")
    
    if not tcp_alive:
        print("No TCP alive proxies found. Stopping.")
        sys.exit(0)
        
    print(f"\nTesting Xray on {len(tcp_alive)} proxies using {XRAY_WORKERS} workers...")
    xray_alive = []
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=XRAY_WORKERS) as executor:
        futures = {executor.submit(test_xray_latency, c, xray_exe): c for c in tcp_alive}
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            config = futures[future]
            ok, lat, reason = future.result()
            
            if ok:
                xray_alive.append(config)
                results.append({"config": config, "status": "SUCCESS", "latency": lat, "reason": reason})
                print(f"  [{i+1}/{len(tcp_alive)}] ✅ Xray Alive | {lat}ms")
            else:
                results.append({"config": config, "status": "FAILED", "reason": reason})
                if (i+1) % 20 == 0:
                    print(f"  [{i+1}/{len(tcp_alive)}] ❌ Failed | Reason: {reason}")
                    
    print(f"\nXray Alive: {len(xray_alive)}/{len(tcp_alive)}")
    
    with open(os.path.join(TEST_DIR, "xray_debug_results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    with open(os.path.join(TEST_DIR, "xray_alive.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(xray_alive))
        
    print(f"\nResults saved to {TEST_DIR}/xray_debug_results.json")
    print(f"Alive configs saved to {TEST_DIR}/xray_alive.txt")
    
    print("\n" + "=" * 60)
    print("Done.")
    print("=" * 60)

if __name__ == "__main__":
    main()