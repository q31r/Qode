# Qode — Automated V2Ray & Free Proxy Collector

Qode is a fully automated, open-source proxy and V2Ray subscription collector. It gathers free proxy servers from dozens of reputable public sources every single day, tests them for real connectivity, and publishes fast, reliable proxy lists for your client.

Whether you need a massive list of raw configs for scraping or a highly vetted list for stable daily browsing, Qode provides tested and categorized **Free V2Ray Configs**, **VLESS**, **VMess**, **Trojan**, **Shadowsocks**, and **Hysteria2** servers.

## 📤 Available Outputs (Proxy Subscriptions)

Every day, GitHub Actions automatically updates the following proxy lists. You can use the raw link of any file as a direct subscription link in your favorite client (like v2rayN, v2rayNG, Nekoray, or Clash):

| File | Description | Health Check Level |
|---|---|---|
| 🥇 **`nodes_top_100.txt`** | **The Elite.** Top 100 fastest and most stable proxies. | Fully verified |
| 🥈 **`nodes_featured.txt`** | **Premium Proxy List.** 5,000 highly vetted proxies. | Passed Xray Test |
| 📦 **`nodes_full.txt`** | **Complete Alive Proxy List.** Every working proxy found. | Passed TCP Liveness Test |

> **Note:** All output files are automatically sorted by network speed and quality, ensuring the fastest and most stable servers appear at the top of the list. Lists are also organized by protocol for easy navigation.

## 🚀 How to use

1. Choose the file you want from the table above based on your needs.
2. Click on the file (e.g., `nodes_top_100.txt`) and click the **Raw** button.
3. Copy the URL of the Raw page.
4. Paste it into your proxy client (V2Ray, Xray, Clash) as a new subscription link and update.

## ⚙️ How it works

Qode runs entirely in GitHub Actions with zero manual intervention, ensuring you always have the freshest free servers:

1. **Fetch & Deduplicate:** Downloads thousands of configs from a secure, encrypted list of public sources and removes duplicates.
2. **TCP Liveness & Speed:** Performs fast TCP port scans to filter out dead nodes and sorts the survivors by connection speed.
3. **Xray Verification (Featured):** Takes the top performers and tests them using the actual Xray core to ensure real internet connectivity, generating a 5,000-node premium list.
4. **Deep Multi-Scan (Top 100):** Subjects the top proxies to consecutive tests to identify the absolute best 100 servers.
5. **Publish:** Commits the refreshed lists back to the repository exactly once a day.

## ⏰ Update Schedule

The entire pipeline (fetching, testing, and publishing) runs **once every 24 hours** via GitHub Actions cron jobs to ensure you always have the freshest free proxy servers.

## 📄 License

MIT