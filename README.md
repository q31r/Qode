# Qode — Automated V2Ray & Free Proxy Collector

<div align="center">
  
[![English](https://img.shields.io/badge/Language-English-blue?style=for-the-badge)](#-english)  [![Persian](https://img.shields.io/badge/Language-Persian-green?style=for-the-badge)](#-persian)

</div>

---

<a id="-english"></a>

## 🇬🇧 English

Qode is a fully automated, open-source proxy and V2Ray subscription collector. It gathers free proxy servers from dozens of reputable public sources every single day, tests them for real connectivity, and publishes fast, reliable proxy lists for your client.

Whether you need a massive list of raw configs for scraping or a highly vetted list for stable daily browsing, Qode provides tested and categorized **Free V2Ray Configs**, **VLESS**, **VMess**, **Trojan**, **Shadowsocks**, and **Hysteria2** servers.

### 📤 Available Outputs (Proxy Subscriptions)

Every day, GitHub Actions automatically updates the following proxy lists. You can use the raw link of any file as a direct subscription link in your favorite client (like v2rayN, v2rayNG, Nekoray, or Clash).

#### 💎 Curated (Hand-picked Sources)
| File | Format | Description |
|---|---|---|
| [nodes_curated.txt](https://raw.githubusercontent.com/q31r/Qode/main/nodes_curated.txt) | Plain Text | Configs from hand-picked and popular sources, verified for TCP connectivity. |
| [nodes_curated_Base64.txt](https://raw.githubusercontent.com/q31r/Qode/main/nodes_curated_Base64.txt) | Base64 | Base64 encoded version for legacy clients compatibility. |

#### 📦 Full (All Sources)
| File | Format | Description |
|---|---|---|
| [nodes_full.txt](https://raw.githubusercontent.com/q31r/Qode/main/nodes_full.txt) | Plain Text | Every working proxy found across all sources, sorted by speed and priority ports. |
| [nodes_full_Base64.txt](https://raw.githubusercontent.com/q31r/Qode/main/nodes_full_Base64.txt) | Base64 | Base64 encoded version for legacy clients compatibility. |

#### 🧪 Personal Collection
| File | Format | Description |
|---|---|---|
| [q31r.txt](https://raw.githubusercontent.com/q31r/Qode/main/q31r.txt) | Plain Text | A hand-picked list of personally tested and verified proxies. |

> **Note:** All output files are automatically sorted first by priority ports (for better stability) and then by TCP latency (for faster connections). So the best and fastest servers always appear at the top of every list.

### 🚀 How to use

1. Choose the file you want from the tables above based on your needs.
2. Click on the file link to open its raw version.
3. Copy the URL from the browser.
4. Paste it into your proxy client (V2Ray, Xray, Clash) as a new subscription link and update.

### ⚙️ How it works

Qode runs entirely in GitHub Actions with zero manual intervention, ensuring you always have the freshest free servers:

1. **Fetch & Validate:** Downloads thousands of configs from dozens of public sources, filters out invalid ones with strict protocol validation, and removes precise duplicates using Protocol, IP, Port, and UUID/Password as the key to keep the list clean.
2. **TCP Liveness & Speed:** Performs fast TCP port scans (with retries and longer timeout for unstable servers) to filter out dead nodes and sorts the survivors by connection speed, so you always get the fastest proxies first.
3. **Priority Port Sorting:** Servers running on standard ports (443, 8443, 2053, etc.) are prioritized and listed at the top, improving stability and bypassing potential ISP restrictions.
4. **Multi-Format Publishing:** Generates both plain text and Base64 encoded outputs to support a wide range of clients, from modern apps to legacy ones.
5. **Automated Reports:** After each run, detailed JSON reports are generated in the `report/` directory, containing statistics about source health, deduplication, and alive proxy counts.

### ⏰ Update Schedule

The entire pipeline (fetching, testing, and publishing) runs **once every 24 hours** via GitHub Actions cron jobs to ensure you always have the freshest free proxy servers. No manual trigger is required — the bot handles everything automatically.

### 🛠️ Features

- ✅ **Fully Automated:** Zero manual intervention — just subscribe and forget.
- 🚀 **High Performance:** Parallel downloading and multi-threaded TCP testing for maximum speed.
- 🎯 **Quality Assured:** Strict validation, precise deduplication, and priority port sorting to keep only the best servers.
- 📦 **Dual Format:** Both plain text and Base64 outputs for maximum client compatibility.
- 📊 **Detailed Reports:** JSON reports for every run to track source health and list quality.
- 🔄 **Daily Updates:** Fresh lists published every 24 hours without any downtime.

### ❓ FAQ

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

<a id="-persian"></a>

<div dir="rtl">

## 🇮🇷 پارسی

Qode یک جمع‌آوری‌کننده سابسکریپشن و پروکسی V2Ray کاملاً خودکار و اپن‌سورس است. این پروژه هر روز از ده‌ها منبع عمومی معتبر، سرورهای پروکسی رایگان را جمع‌آوری می‌کند، آن‌ها را از نظر اتصال واقعی تست می‌کند و لیست‌های پروکسی سریع و قابل‌اعتماد را برای کلاینت شما منتشر می‌کند.

چه به یک لیست بزرگ از کانفیگ‌های خام برای اسکرپینگ نیاز داشته باشید و چه به یک لیست باکیفیت و تست‌شده برای وب‌گردی پایدار روزانه، Qode سرورهای **V2Ray رایگان**، **VLESS**، **VMess**، **Trojan**، **Shadowsocks** و **Hysteria2** را به صورت تست‌شده و دسته‌بندی‌شده در اختیار شما قرار می‌دهد.

### 📤 خروجی‌های موجود (سابسکریپشن‌های پروکسی)

هر روز، GitHub Actions به طور خودکار لیست‌های پروکسی زیر را به‌روزرسانی می‌کند. شما می‌توانید از لینک Raw هر فایل به عنوان لینک سابسکریپشن مستقیم در کلاینت محبوب خود (مثل v2rayN، v2rayNG، Nekoray یا Clash) استفاده کنید.

#### 💎 دست‌چین شده (منابع منتخب)
| فایل | فرمت | توضیحات |
|---|---|---|
| [nodes_curated.txt](https://raw.githubusercontent.com/q31r/Qode/main/nodes_curated.txt) | متن ساده | کانفیگ‌های منابع دست‌چین شده و محبوب، تست‌شده برای اتصال TCP. |
| [nodes_curated_Base64.txt](https://raw.githubusercontent.com/q31r/Qode/main/nodes_curated_Base64.txt) | Base64 | نسخه کدگذاری‌شده با Base64 برای سازگاری با کلاینت‌های قدیمی. |

#### 📦 کامل (تمام منابع)
| فایل | فرمت | توضیحات |
|---|---|---|
| [nodes_full.txt](https://raw.githubusercontent.com/q31r/Qode/main/nodes_full.txt) | متن ساده | تمام پروکسی‌های سالم پیدا شده از همه منابع، مرتب‌شده بر اساس سرعت و پورت‌های اولویت‌دار. |
| [nodes_full_Base64.txt](https://raw.githubusercontent.com/q31r/Qode/main/nodes_full_Base64.txt) | Base64 | نسخه کدگذاری‌شده با Base64 برای سازگاری با کلاینت‌های قدیمی. |

#### 🧪 مجموعه شخصی
| فایل | فرمت | توضیحات |
|---|---|---|
| [q31r.txt](https://raw.githubusercontent.com/q31r/Qode/main/q31r.txt) | متن ساده | لیستی دست‌چین شده از پروکسی‌های تست‌شده و تأییدشده شخصی. |

> **نکته:** تمام فایل‌های خروجی ابتدا بر اساس پورت‌های اولویت‌دار (برای پایداری بیشتر) و سپس بر اساس تأخیر TCP (برای اتصال سریع‌تر) مرتب می‌شوند. بنابراین بهترین و سریع‌ترین سرورها همیشه در بالای هر لیست قرار می‌گیرند.

### 🚀 نحوه استفاده

1. فایل مورد نظر خود را از جدول‌های بالا بر اساس نیاز خود انتخاب کنید.
2. روی لینک فایل کلیک کنید تا نسخه Raw آن باز شود.
3. URL را از مرورگر کپی کنید.
4. آن را به عنوان لینک سابسکریپشن جدید در کلاینت پروکسی خود (V2Ray، Xray، Clash) وارد کنید و به‌روزرسانی کنید.

### ⚙️ نحوه کار

Qode کاملاً در GitHub Actions اجرا می‌شود و هیچ دخالت دستی نیاز ندارد، بنابراین همیشه تازه‌ترین سرورهای رایگان را دارید:

1. **دریافت و اعتبارسنجی:** هزاران کانفیگ از ده‌ها منبع عمومی دانلود می‌کند، کانفیگ‌های نامعتبر را با اعتبارسنجی سخت‌گیرانه پروتکل حذف می‌کند و تکراری‌های دقیق را با استفاده از پروتکل، IP، پورت و UUID/پسورد به عنوان کلید حذف می‌کند تا لیست تمیز بماند.
2. **تست زنده بودن TCP و سرعت:** اسکن سریع پورت TCP را انجام می‌دهد (با تلاش مجدد و تایم‌اوت بیشتر برای سرورهای ناپایدار) تا نودهای مرده را فیلتر کند و بازمانده‌ها را بر اساس سرعت اتصال مرتب می‌کند، بنابراین همیشه سریع‌ترین پروکسی‌ها را اول دریافت می‌کنید.
3. **مرتب‌سازی بر اساس پورت اولویت‌دار:** سرورهایی که روی پورت‌های استاندارد (443، 8443، 2053 و غیره) اجرا می‌شوند، اولویت داده شده و در بالای لیست قرار می‌گیرند، که باعث بهبود پایداری و دور زدن محدودیت‌های احتمالی ISP می‌شود.
4. **انتشار چند فرمتی:** هم خروجی متن ساده و هم Base64 را برای پشتیبانی از طیف گسترده‌ای از کلاینت‌ها، از اپلیکیشن‌های مدرن تا کلاینت‌های قدیمی، تولید می‌کند.
5. **گزارش‌های خودکار:** پس از هر اجرا، گزارش‌های JSON دقیق در پوشه `report/` تولید می‌شوند که شامل آمار مربوط به سلامت منابع، حذف تکراری و تعداد پروکسی‌های زنده است.

### ⏰ زمان‌بندی به‌روزرسانی

کل خط لوله (دریافت، تست و انتشار) **هر ۲۴ ساعت یک بار** از طریق cron jobهای GitHub Actions اجرا می‌شود تا اطمینان حاصل شود که همیشه تازه‌ترین سرورهای پروکسی رایگان را دارید. هیچ تریگر دستی لازم نیست — ربات همه چیز را به طور خودکار انجام می‌دهد.

### 🛠️ ویژگی‌ها

- ✅ **کاملاً خودکار:** هیچ دخالت دستی لازم نیست — فقط سابسکریپشن کنید و فراموش کنید.
- 🚀 **عملکرد بالا:** دانلود موازی و تست TCP چند رشته‌ای برای حداکثر سرعت.
- 🎯 **تضمین کیفیت:** اعتبارسنجی سخت‌گیرانه، حذف تکراری دقیق و مرتب‌سازی بر اساس پورت اولویت‌دار برای نگه‌داشتن فقط بهترین سرورها.
- 📦 **دو فرمت:** خروجی متن ساده و Base64 برای حداکثر سازگاری با کلاینت.
- 📊 **گزارش‌های دقیق:** گزارش‌های JSON برای هر اجرا برای پیگیری سلامت منابع و کیفیت لیست.
- 🔄 **به‌روزرسانی روزانه:** لیست‌های تازه هر ۲۴ ساعت یک بار بدون هیچ توقف منتشر می‌شوند.

### ❓ سوالات متداول

**س: لیست‌ها چند وقت یک بار به‌روزرسانی می‌شوند؟**
ج: هر ۲۴ ساعت به طور خودکار از طریق GitHub Actions.

**س: از کدام فایل استفاده کنم؟**
ج: اگر یک لیست کوچک‌تر و دست‌چین شده می‌خواهید از `nodes_curated.txt` استفاده کنید. اگر گسترده‌ترین انتخاب ممکن را می‌خواهید از `nodes_full.txt` استفاده کنید.

**س: چرا بعضی سرورها دو بار لیست شده‌اند؟**
ج: UUID یا پسوردهای متفاوت روی یک IP به معنای سرورهای متفاوت است. ما همه را نگه می‌داریم تا گزینه‌های بیشتری داشته باشید.

**س: فایل Base64 در کلاینت من بارگذاری نمی‌شود.**
ج: بعضی کلاینت‌ها به نسخه متن ساده نیاز دارند. به جای آن `nodes_full.txt` یا `nodes_curated.txt` را امتحان کنید.

**س: می‌توانم منابعی مشارکت کنم؟**
ج: بله! یک pull request باز کنید و منبع خود را به لیست اضافه کنید. مطمئن شوید که یک URL عمومی معتبر است.

</div>

---

## 📄 License

MIT