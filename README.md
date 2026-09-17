# 🚌 Bus Geo-Fence Alert

A lightweight Python daemon that tracks a bus in real-time using the LocoNav API and **alerts you on your phone via [ntfy](https://ntfy.sh)** when the bus enters a configurable radius around your home. Designed to be triggered by `cron` — it starts at a scheduled time, fires alerts when the bus is near, and exits automatically.

---

## How It Works

```
cron (scheduled time)
  └─▶ python main.py starts
        └─▶ polls LocoNav API every N seconds
              └─▶ calculates distance from home using Haversine formula
                    ├─▶ bus inside geo-fence → 🔔 ntfy alert on phone
                    │     └─▶ re-alerts every REPEAT_ALERT_INTERVAL polls while bus stays inside
                    │     └─▶ exits after MAX_ALERTS notifications
                    └─▶ bus outside geo-fence → waits and retries
                          └─▶ exits after MAX_RUNTIME_MINUTES regardless
```

**Exit conditions (whichever comes first):**
- `MAX_ALERTS` notifications have been fired
- `MAX_RUNTIME_MINUTES` has elapsed (safety timeout — bus may be stationary or delayed)

---

## Project Structure

```
bus-alert/
├── main.py               # Main polling loop and alert logic
├── geo.py                # Haversine distance calculation (pure Python)
├── notifiers/
│   ├── ntfy.py           # ntfy.sh push notification (primary — rings phone)
│   ├── telegram.py       # Telegram Bot alert (optional)
│   ├── desktop.py        # Desktop OS notification (optional)
│   └── email_notify.py   # SMTP email alert (optional)
├── tests/
│   └── test_geo.py       # Unit tests for Haversine distance
├── .env.example          # Configuration template — copy to .env
├── .env                  # Your secrets and settings (never committed)
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── run_phone.sh          # Wrapper script for Termux (Android)
├── run_comp.sh           # Wrapper script for laptop/macOS
└── cron.txt              # Reference cron schedule entries
```

---

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
nano .env   # or use any text editor
```

### All Configuration Options

| Variable | Required | Default | Description |
|---|---|---|---|
| `BUS_API_URL` | ✅ | — | LocoNav tracking API URL for your bus |
| `HOME_LAT` | ✅ | — | Your home latitude |
| `HOME_LONG` | ✅ | — | Your home longitude |
| `GEOFENCE_RADIUS_KM` | ✅ | — | Alert when bus is within this radius (km) |
| `NTFY_TOPIC` | ✅ | — | Your unique ntfy.sh topic name |
| `POLL_INTERVAL_SECONDS` | ❌ | `60` | How often to call the bus API (seconds) |
| `REPEAT_ALERT_INTERVAL` | ❌ | `5` | Re-alert every N polls while bus stays inside fence |
| `MAX_ALERTS` | ❌ | `3` | Exit after firing this many alerts |
| `MAX_RUNTIME_MINUTES` | ❌ | `30` | Exit after this many minutes regardless of alerts |
| `TELEGRAM_BOT_TOKEN` | ❌ | — | Telegram bot token (from @BotFather) |
| `TELEGRAM_CHAT_ID` | ❌ | — | Your Telegram chat ID |
| `SMTP_HOST` | ❌ | — | SMTP server (e.g. smtp.gmail.com) |
| `SMTP_PORT` | ❌ | `587` | SMTP port |
| `SMTP_USER` | ❌ | — | SMTP username / email address |
| `SMTP_PASSWORD` | ❌ | — | SMTP password or Gmail App Password |
| `ALERT_EMAIL_TO` | ❌ | — | Recipient email address |

### Tips

- **Home coordinates:** Open Google Maps → long-press your home location → coordinates appear at the top
- **`GEOFENCE_RADIUS_KM`:** Start with `1.0` (1 km). Increase if you want earlier alerts
- **`POLL_INTERVAL_SECONDS=10` + `REPEAT_ALERT_INTERVAL=3`** = alert every 30 seconds while bus is near
- **`MAX_RUNTIME_MINUTES=30`** ensures the daemon always exits within 30 minutes even if the bus never comes

---

## Alert Channel: ntfy.sh

The primary alert channel is **[ntfy](https://ntfy.sh)** — a free, open-source push notification service. It rings your phone with an urgent notification that bypasses silent mode.

### Phone Setup (one time)

1. Install the **ntfy** app:
   - Android: [Play Store → ntfy](https://play.google.com/store/apps/details?id=io.heckel.ntfy)
   - iOS: [App Store → ntfy](https://apps.apple.com/app/ntfy/id1625396347)

2. Open the app → tap **+** → enter your chosen topic name (e.g. `my-bus-alert-abc123`)
   > ⚠️ Keep the topic name hard to guess — it acts as your private channel

3. Allow notifications when prompted

4. Set a loud ringtone: long-press your topic → **Edit** → **Notification sound**

5. Enable **Do Not Disturb override** so it rings even on silent mode

6. Add your topic name to `.env`:
   ```dotenv
   NTFY_TOPIC=my-bus-alert-abc123
   ```

### Quick Test (no code needed)

Verify your phone receives a notification:
```bash
curl -d "Test from laptop" -H "Priority: urgent" ntfy.sh/my-bus-alert-abc123
```

---

## Setup on Laptop (macOS/Linux)

### Prerequisites
- Python 3.9+
- `uv` (recommended) or `pip`

### Install with uv
```bash
# Install uv if not already installed
curl -Ls https://astral.sh/uv/install.sh | sh

cd bus-alert
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Install with pip
```bash
cd bus-alert
pip install -r requirements.txt
```

### Configure
```bash
cp .env.example .env
# Edit .env with your values
```

---

## Setup on Android Phone (Termux)

> **Important:** Install Termux from the **Play Store**. Do not use F-Droid if you prefer Play Store.

### Step 1: Install Python in Termux
```bash
pkg update && pkg upgrade -y
pkg install python git -y
```

### Step 2: Clone the repo
```bash
git clone https://github.com/SriniRDev/bus-alert.git ~/bus-alert
cd ~/bus-alert
```

### Step 3: Install dependencies
```bash
pip install requests python-dotenv plyer
```

### Step 4: Configure
```bash
cp .env.example .env
nano .env
# Fill in your BUS_API_URL, HOME_LAT, HOME_LONG, GEOFENCE_RADIUS_KM, NTFY_TOPIC
```

### Step 5: Make run script executable
```bash
chmod +x run_phone.sh
```

### Step 6: Disable battery optimization for Termux
This is **critical** — Android kills background processes otherwise.

- **Settings → Apps → Termux → Battery → Unrestricted**
  *(exact path varies by phone brand: Samsung/Xiaomi may show "Allow background activity")*

---

## Running the Application

### Dry Run (no real alerts — safe for testing)

Tests the full flow using live API data but prints alerts to console instead of sending them.

**On laptop:**
```bash
source .venv/bin/activate   # if using venv
python3 main.py --dry-run
```

**On Termux:**
```bash
cd ~/bus-alert
python3 main.py --dry-run
```

Expected output:
```
2026-09-17 07:30:00 [INFO] Daemon started. Will exit after 3 alert(s) or 30 minutes.
2026-09-17 07:30:00 [INFO] Home: (12.938230, 77.701103)  Radius: 1.00 km  Poll: 10s  Repeat every: 3 polls
2026-09-17 07:30:01 [INFO] Bus KA00AA0000 — 0.85 km from home
2026-09-17 07:30:01 [INFO] Alert 1/3 — bus inside fence for 1 poll(s).
[DRY-RUN] Would fire alerts:
  Title: 🚌 KA00AA0000 is approaching! (1/3)
  Body:
  Distance: 0.85 km from home
  Address: Sarjapur Road, Bellandur, Bengaluru
  Speed: 12 km/h | Status: Moving
```

### Run Live

**On laptop (using wrapper script):**
```bash
bash run_comp.sh
```

**On Termux (using wrapper script):**
```bash
bash run_phone.sh
```

**Or run directly:**
```bash
python3 main.py
```

### Watch Logs Live

Two log files are maintained:

| File | Contents |
|---|---|
| `python-bus-alert.log` | Structured Python logs (rotating, max 1MB × 3 backups) |
| `bus-alert.log` | Console stdout captured by the run scripts |

```bash
# Watch Python logs in real time
tail -f python-bus-alert.log

# Watch console logs
tail -f bus-alert.log
```

### Stop the Daemon
```bash
pkill -f "python main.py"

# Verify it stopped
pgrep -f "python main.py" && echo "still running" || echo "stopped"
```

---

## Scheduling with Cron (Termux)

Run the daemon automatically at your commute times — it starts, watches for the bus, and exits on its own.

### Step 1: Install cronie
```bash
pkg install cronie -y
```

### Step 2: Start the cron daemon
```bash
crond
```
> Run `crond` once each time you open Termux. Keep Termux running in the background.

### Step 3: Edit crontab
```bash
crontab -e
```

Add your schedule (see `cron.txt` for reference):
```
# Morning commute — weekdays at 7:00 AM
00 07 * * 1-5 /data/data/com.termux/files/home/bus-alert/run_phone.sh

# Evening commute — weekdays at 3:25 PM
25 15 * * 1-5 /data/data/com.termux/files/home/bus-alert/run_phone.sh
```

### Cron Schedule Format
```
MIN HOUR DAY MONTH WEEKDAY   command
 0    7   *    *    1-5      → 7:00 AM, Monday to Friday
25   15   *    *    1-5      → 3:25 PM, Monday to Friday
 0    8   *    *    *        → 8:00 AM, every day
```

### Step 4: Verify cron is working
```bash
# Check crond is running
pgrep crond && echo "crond is running" || echo "not running — type: crond"

# List current cron jobs
crontab -l
```

### Pull latest changes before cron runs
After any updates on laptop, pull on phone:
```bash
cd ~/bus-alert && git pull
```

---

## Running Tests

Unit tests cover the Haversine distance calculation in `geo.py`.

```bash
# Install pytest if not already installed
pip install pytest

# Run tests
python3 -m pytest tests/ -v
```

Expected output:
```
tests/test_geo.py::test_same_point_is_zero     PASSED
tests/test_geo.py::test_known_distance_approx  PASSED
tests/test_geo.py::test_symmetry               PASSED
tests/test_geo.py::test_distance_is_positive   PASSED
tests/test_geo.py::test_bus_within_geofence    PASSED

5 passed in 0.02s
```

---

## Typical Alert on Phone

```
🚨 Urgent · ntfy

🚌 KA00AA0000 is approaching! (1/3)
Distance: 0.85 km from home
Address: Sarjapur Road, Bellandur, Bengaluru
Speed: 12 km/h | Status: Moving
```

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Only 1 notification received | Bus stayed inside fence; repeat interval not reached yet | Wait for `POLL_INTERVAL × REPEAT_ALERT_INTERVAL` seconds, or reduce `REPEAT_ALERT_INTERVAL` |
| No notifications at all | Bus outside geo-fence the whole time | Increase `GEOFENCE_RADIUS_KM` or verify coordinates |
| Daemon runs forever | Bus is stationary outside fence | `MAX_RUNTIME_MINUTES` will auto-exit it (default 30 min) |
| `python: command not found` | macOS/Termux uses `python3` | Use `python3 main.py` or check `run_phone.sh` uses `python3` |
| `.venv/bin/activate not found` | venv was created on laptop, not on phone | On Termux, skip venv — use system pip directly |
| cron job not triggering | crond not running | Run `crond` in Termux and keep Termux open |
| Android kills Termux | Battery optimization enabled | Settings → Apps → Termux → Battery → Unrestricted |
| API request failed | Network issue or API token invalid | Check `BUS_API_URL` in `.env` and internet connectivity |

---

## Security Notes

- `.env` is listed in `.gitignore` — it is **never committed** to git
- Your home coordinates and API token live only in `.env` on your device
- The ntfy topic name acts as a private channel — keep it unique and hard to guess
- Log files (`*.log`) are also excluded from git
