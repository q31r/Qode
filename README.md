# Qode — Automated V2Ray & Free Proxy Collector

Qode is a fully automated, open-source proxy and V2Ray subscription collector. It gathers free proxy servers from dozens of reputable public sources every single day, tests them for real connectivity, and publishes fast, reliable proxy lists for your client.

Whether you need a massive list of raw configs for scraping or a highly vetted list for stable daily browsing, Qode provides tested and categorized **Free V2Ray Configs**, **VLESS**, **VMess**, **Trojan**, **Shadowsocks**, and **Hysteria2** servers.

---

## 📤 Available Outputs (Proxy Subscriptions)

Every day, GitHub Actions automatically updates the following proxy lists. You can use the raw link of any file as a direct subscription link in your favorite client (like v2rayN, v2rayNG, Nekoray, or Clash).

### 💎 Curated (Hand-picked Sources)
| File | Format | Description |
|---|---|---|
| [nodes_curated.txt](https://raw.githubusercontent.com/q31r/Qode/main/nodes_curated.txt) | Plain Text | Configs from hand-picked and popular sources, verified for TCP connectivity. |
| [nodes_curated_Base64.txt](https://raw.githubusercontent.com/q31r/Qode/main/nodes_curated_Base64.txt) | Base64 | Base64 encoded version for legacy clients compatibility. |

### 📦 Full (All Sources)
| File | Format | Description |
|---|---|---|
| [nodes_full.txt](https://raw.githubusercontent.com/q31r/Qode/main/nodes_full.txt) | Plain Text | Every working proxy found across all sources, sorted by speed and priority ports. |
| [nodes_full_Base64.txt](https://raw.githubusercontent.com/q31r/Qode/main/nodes_full_Base64.txt) | Base64 | Base64 encoded version for legacy clients compatibility. |

> **Note:** All output files are automatically sorted first by priority ports (for better stability) and then by TCP latency (for faster connections). So the best and fastest servers always appear at the top of every list.

---

## 🚀 How to use

1. Choose the file you want from the tables above based on your needs.
2. Click on the file link to open its raw version.
3. Copy the URL from the browser.
4. Paste it into your proxy client (V2Ray, Xray, Clash) as a new subscription link and update.

---

## ⚙️ How it works

Qode runs entirely in GitHub Actions with zero manual intervention, ensuring you always have the freshest free servers:

1. **Fetch & Deduplicate:** Downloads thousands of configs from dozens of public sources and removes precise duplicates using Protocol, IP, Port, and UUID/Password as the key to keep the list clean.
2. **TCP Liveness & Speed:** Performs fast TCP port scans to filter out dead nodes and sorts the survivors by connection speed, so you always get the fastest proxies first.
3. **Priority Port Sorting:** Servers running on standard ports (443, 8443, 2053, etc.) are prioritized and listed at the top, improving stability and bypassing potential ISP restrictions.
4. **Multi-Format Publishing:** Generates both plain text and Base64 encoded outputs to support a wide range of clients, from modern apps to legacy ones.
5. **Automated Reports:** After each run, detailed JSON reports are generated in the `report/` directory, containing statistics about source health, deduplication, and alive proxy counts.

---

## ⏰ Update Schedule

The entire pipeline (fetching, testing, and publishing) runs **once every 24 hours** via GitHub Actions cron jobs to ensure you always have the freshest free proxy servers. No manual trigger is required — the bot handles everything automatically.

---

## 🛠️ Features

- ✅ **Fully Automated:** Zero manual intervention — just subscribe and forget.
- 🚀 **High Performance:** Parallel downloading and multi-threaded TCP testing for maximum speed.
- 🎯 **Quality Assured:** Precise deduplication and priority port sorting to keep only the best servers.
- 📦 **Dual Format:** Both plain text and Base64 outputs for maximum client compatibility.
- 📊 **Detailed Reports:** JSON reports for every run to track source health and list quality.
- 🔄 **Daily Updates:** Fresh lists published every 24 hours without any downtime.

---

## ❓ FAQ

**Q: How often are the lists updated?**
A: Every 24 hours automatically via GitHub Actions.

**Q: Which file should I use?**
A: Use `nodes_curated.txt` if you want a smaller, hand-picked list. Use `nodes_full.txt` if you want the widest selection possible.

**Q: Why are some servers listed twice?**
A: Different UUIDs or passwords on the same IP mean they are distinct servers. We keep them all so you have more options.

**Q: The Base64 file won't load in my client.**
A: Some clients require the plain text version. Try `nodes_full.txt` or `nodes_curated.txt` instead.

**Q: Can I contribute sources?**
A: Yes! Open a pull request and add your source to the list. Make sure it's a valid public URL.

---

## 📄 License

MIT