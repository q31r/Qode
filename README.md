# Qode — Automated V2Ray & Free Proxy Collector

Qode is a fully automated, open-source proxy and V2Ray subscription collector. It gathers free proxy servers from dozens of reputable public sources every single day, tests them for real connectivity, and publishes fast, reliable proxy lists for your client.

Whether you need a massive list of raw configs for scraping or a highly vetted list for stable daily browsing, Qode provides tested and categorized **Free V2Ray Configs**, **VLESS**, **VMess**, **Trojan**, **Shadowsocks**, and **Hysteria2** servers.

## 📤 Available Outputs (Proxy Subscriptions)

Every day, GitHub Actions automatically updates the following proxy lists. You can use the raw link of any file as a direct subscription link in your favorite client (like v2rayN, v2rayNG, Nekoray, or Clash):

| File | Description | Health Check Level |
|---|---|---|
| 💎 **`nodes_curated.txt`** | **Hand-picked Premium List.** Raw configs from hand-picked and popular sources. | No scan (Direct raw) |
| ⭐ **`nodes_featured.txt`** | **Verified Proxy List.** Proxies that successfully passed real internet connectivity. | Passed Xray Test |
| 📦 **`nodes_full.txt`** | **Complete Alive Proxy List.** Every working proxy found across all sources. | Passed TCP Liveness Test |

> **Note:** All output files are automatically sorted by network speed and quality, ensuring the fastest and most stable servers appear at the top of the list. Lists are also organized by protocol for easy navigation.

## 🚀 How to use

1. Choose the file you want from the table above based on your needs.
2. Click on the file (e.g., `nodes_featured.txt`) and click the **Raw** button.
3. Copy the URL of the Raw page.
4. Paste it into your proxy client (V2Ray, Xray, Clash) as a new subscription link and update.

## ⚙️ How it works

Qode runs entirely in GitHub Actions with zero manual intervention, ensuring you always have the freshest free servers:

1. **Fetch & Deduplicate:** Downloads thousands of configs from a secure, encrypted list of public sources and removes duplicates.
2. **Curated Extraction:** Directly extracts and publishes configs from hand-picked and popular sources without any testing.
3. **TCP Liveness & Speed:** Performs fast TCP port scans across all sources to filter out dead nodes and sorts the survivors by connection speed.
4. **Xray Verification (Featured):** Tests every alive proxy using the actual Xray core to ensure real internet connectivity, generating a highly vetted premium list.
5. **Publish:** Commits the refreshed lists back to the repository exactly once a day.

## ⏰ Update Schedule

The entire pipeline (fetching, testing, and publishing) runs **once every 24 hours** via GitHub Actions cron jobs to ensure you always have the freshest free proxy servers.

## 📄 License

MIT