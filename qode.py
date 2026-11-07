import os
import sys
import json
import time
import base64
import hashlib
import requests
from datetime import datetime, timezone
from cryptography.fernet import Fernet

SOURCES_FILE = "sources.enc"
OUTPUT_FEATURED = "nodes_featured_12h.txt"
OUTPUT_FULL     = "nodes_full_24h.txt"
REPORT_DIR      = "report"
REPORT_FEATURED = os.path.join(REPORT_DIR, "featured.json")
REPORT_FULL     = os.path.join(REPORT_DIR, "full.json")

TIMEOUT = 30
MAX_RETRIES = 2
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

_FAKE_NAMES = [
    "Server List Alpha", "Global Nodes Cluster", "Premium Edge Pool",
    "Enterprise Relay Group", "Optimized Backbone Set", "Secure Tunnel Archive",
    "Public Access Nodes", "High-Speed Core Bundle", "Distributed Mesh Pool",
    "Load-Balanced Node Set", "Fallback Route Collection", "Regional Exit Nodes",
    "Balanced Throughput Set", "Multi-Path Relay Bundle", "Tier-One Network Pool",
    "Resilient Uplink Archive", "Redundant Node Cluster", "Low-Latency Group",
    "Backup Edge Collection", "Extended Route Set", "Cloud Relay Assembly",
    "Primary Backbone Nodes", "Secondary Access Pool", "Premium Uplink Bundle",
    "Dedicated Node Archive", "Unified Proxy Pool", "Consolidated Relay Set",
]


def fake_name(index: int, url: str) -> str:
    h = hashlib.sha256(url.encode()).digest()
    base = _FAKE_NAMES[h[0] % len(_FAKE_NAMES)]
    return f"{base} {index}"


def classify_error(exc: Exception | None, status: int | None = None) -> str:
    if status is not None:
        return f"http_{status}"
    if exc is None:
        return "unknown"
    name = type(exc).__name__
    if "Timeout" in name:
        return "timeout"
    if "ConnectionError" in name or "Connect" in name:
        return "connection_failed"
    if "InvalidURL" in name or "MissingSchema" in name:
        return "invalid_url"
    return "request_failed"


def load_sources() -> tuple[list[str], list[str]]:
    password = os.environ["SOURCES_KEY"].encode()
    key = base64.urlsafe_b64encode(password.ljust(32)[:32])
    cipher = Fernet(key)

    with open(SOURCES_FILE, "rb") as f:
        encrypted = f.read()

    plaintext = cipher.decrypt(encrypted).decode("utf-8")

    featured: list[str] = []
    full: list[str] = []
    seen: set[str] = set()

    for line in plaintext.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        is_featured = line.startswith("*")
        if is_featured:
            line = line[1:].strip()

        if not line.startswith(("http://", "https://")):
            continue
        if line in seen:
            continue
        seen.add(line)

        full.append(line)
        if is_featured:
            featured.append(line)

    return featured, full


def download_source(url: str) -> tuple[list[str], bool, str]:
    last_err = "unknown"
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(
                url,
                timeout=TIMEOUT,
                headers={"User-Agent": USER_AGENT},
            )
            if r.status_code == 200:
                configs = []
                for line in r.text.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if any(line.startswith(p) for p in (
                        "vless://", "vmess://", "trojan://", "ss://",
                        "socks5://"
                    )):
                        configs.append(line)
                return configs, True, ""
            last_err = classify_error(None, r.status_code)
        except Exception as e:
            last_err = classify_error(e)
        if attempt < MAX_RETRIES - 1:
            time.sleep(1.0)
    return [], False, last_err


def collect_batch(sources: list[str], label: str) -> tuple[list[str], dict]:
    started_at = time.time()
    started_iso = datetime.now(timezone.utc).isoformat()

    print("=" * 60)
    print(f"Qode — {label}  ({len(sources)} sources)")
    print("=" * 60)

    all_configs: list[str] = []
    seen: set[str] = set()
    failed: list[dict] = []
    succeeded = 0
    raw_total = 0

    for i, url in enumerate(sources, 1):
        name = fake_name(i, url)
        print(f"[{i:02d}/{len(sources):02d}] {name} downloading...", end=" ", flush=True)

        configs, ok, err = download_source(url)

        if ok:
            raw_total += len(configs)
            new = 0
            for c in configs:
                if c not in seen:
                    seen.add(c)
                    all_configs.append(c)
                    new += 1
            succeeded += 1
            print(f"+{new} new (total: {len(all_configs)})")
        else:
            failed.append({"id": i, "name": name, "error": err})
            print(f"{err}")

    proto_counts: dict[str, int] = {}
    for c in all_configs:
        for p in ("vless", "vmess", "trojan", "ss", "socks5"):
            if c.startswith(p + "://"):
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
        "duplicates_removed": max(0, raw_total - len(all_configs)),
        "failed_sources": failed,
        "protocol_breakdown": proto_counts,
    }

    return all_configs, report


def main():
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "both"
    if mode not in ("featured", "full", "both"):
        print(f"Unknown mode: {mode}")
        sys.exit(1)

    featured, full = load_sources()

    print(f"Loaded: {len(featured)} featured, {len(full)} total\n")

    os.makedirs(REPORT_DIR, exist_ok=True)

    if mode in ("featured", "both"):
        configs, report = collect_batch(featured, "featured-12h")
        with open(OUTPUT_FEATURED, "w", encoding="utf-8") as f:
            f.write("\n".join(configs))
        with open(REPORT_FEATURED, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n→ {OUTPUT_FEATURED}  ({len(configs)} configs)")
        print(f"→ {REPORT_FEATURED}\n")

    if mode in ("full", "both"):
        configs, report = collect_batch(full, "full-24h")
        with open(OUTPUT_FULL, "w", encoding="utf-8") as f:
            f.write("\n".join(configs))
        with open(REPORT_FULL, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n→ {OUTPUT_FULL}  ({len(configs)} configs)")
        print(f"→ {REPORT_FULL}\n")

    print("=" * 60)
    print("Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()