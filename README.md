# Qode — Automated V2Ray & Free Proxy Collector

Qode is a fully automated, open-source proxy and V2Ray subscription collector. It gathers free proxy servers from dozens of reputable public sources every single day, tests them for real connectivity, and publishes fast, reliable proxy lists for your client.

Whether you need a massive list of raw configs for scraping or a highly vetted list for stable daily browsing, Qode provides tested and categorized **Free V2Ray Configs**, **VLESS**, **VMess**, **Trojan**, **Shadowsocks**, and **Hysteria2** servers.

## 📤 Available Outputs (Proxy Subscriptions)

Every day, GitHub Actions automatically updates the following proxy lists. You can use the raw link of any file as a direct subscription link in your favorite client (like v2rayN, v2rayNG, Nekoray, or Clash):

| File | Description | Health Check Level |
|---|---|---|
| 🟢 **`nodes_featured.txt`** | **Premium Proxy List.** The best of the best, sourced from trusted providers. | Passed TCP + Real Xray Test |
| 🔵 **`nodes_5k.txt`** | Top 5,000 active proxies for fast and reliable browsing. | Random sample from 10K alive list |
| 🟡 **`nodes_10k.txt`** | Up to 10,000 active proxies for a vast selection of choices. | Random sample from Alive list |
| ⚪ **`nodes_full.txt`** | **Complete Alive Proxy List.** Every working proxy found across all sources. | Passed TCP Liveness Test |

> **Note:** All output files are automatically sorted by protocol (VLESS, VMess, Trojan, etc.) so the lists are clean, organized, and easy to navigate.

## 🚀 How to use

1. Choose the file you want from the table above based on your needs.
2. Click on the file (e.g., `nodes_featured.txt`) and click the **Raw** button.
3. Copy the URL of the Raw page.
4. Paste it into your proxy client (V2Ray, Xray, Clash) as a new subscription link and update.

## ⚙️ How it works

Qode runs entirely in GitHub Actions with zero manual intervention, ensuring you always have the freshest free servers:

1. **Fetch:** Downloads thousands of configs from a secure, encrypted list of public sources.
2. **Deduplicate:** Removes duplicate server configurations to keep the lists clean.
3. **Benchmark:** Automatically tests the GitHub runner's network speed to optimize concurrency and prevent crashes.
4. **TCP Liveness:** Performs fast TCP port scans across all servers to filter out dead nodes.
5. **Xray Verification:** Spawns the actual Xray core directly inside the runner to test real internet connectivity for the Premium `featured` list.
6. **Publish:** Sorts the results by protocol and commits the refreshed lists back to the repository exactly once a day.

## ⏰ Update Schedule

The entire pipeline (fetching, TCP testing, Xray testing, and publishing) runs **once every 24 hours** via GitHub Actions cron jobs to ensure you always have the freshest free proxy servers without hitting rate limits.

## 📄 License

MIT