# Qode

Automated proxy collector — publishes fresh curated and full proxy lists on a 12h / 24h schedule.

## 📤 Outputs

| File | Description | Updated |
|---|---|---|
| `nodes_featured_12h.txt` | Curated selection of configs | Every 12 hours |
| `nodes_full_24h.txt` | Complete collection of configs | Every 24 hours |

## 🚀 How to use

Each output file contains one proxy config per line, in plain URI format:

vless://...
vmess://...
trojan://...
ss://...

Just download the file you need and import it into your client. No setup, no account, no extra steps.

## 🎯 Which file should I use?

- 🟢 **`nodes_featured_12h.txt`** — a smaller, curated list. Best if you want quality over quantity. Refreshed every 12 hours.
- 🔵 **`nodes_full_24h.txt`** — the complete collection. Best if you want the widest possible selection. Refreshed once a day.

## ⏰ Update schedule

| File | Updated |
|---|---|
| `nodes_featured_12h.txt` | Every 12 hours |
| `nodes_full_24h.txt` | Every 24 hours |

Files are updated automatically — just grab the latest version whenever you need it.

## 📄 License

MIT