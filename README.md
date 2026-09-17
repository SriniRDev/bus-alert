# Bus Geo-Fence Alert

A Python daemon that polls a LocoNav bus tracking API and fires alerts (desktop, Telegram, email) when the bus enters a configurable geo-fence radius around your home.

## Requirements
- Python 3.9+
- [uv](https://github.com/astral-sh/uv) — fast Python package manager

## Setup

```bash
# 1. Install uv (if not already installed)
curl -Ls https://astral.sh/uv/install.sh | sh

# 2. Create virtual environment
cd bus_alert
uv venv

# 3. Activate it
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

# 4. Install dependencies
uv pip install -r requirements.txt

# 5. Configure
cp .env.example .env
# Edit .env with your home coordinates, Telegram token, and email credentials
```

## Configuration (`.env`)

| Variable | Description |
|---|---|
| `BUS_API_URL` | LocoNav tracking API URL |
| `HOME_LAT` / `HOME_LONG` | Your home coordinates |
| `GEOFENCE_RADIUS_KM` | Alert when bus is within this radius |
| `POLL_INTERVAL_SECONDS` | How often to check (default: 60) |
| `TELEGRAM_BOT_TOKEN` | From [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |
| `SMTP_HOST/PORT/USER/PASSWORD` | SMTP email settings |
| `ALERT_EMAIL_TO` | Recipient email address |

## Usage

```bash
# Run the daemon
python main.py

# Test without sending real alerts
python main.py --dry-run
```

## Alert Channels

- **Desktop** — OS-level notification (macOS, Windows, Linux)
- **Telegram** — Message via Telegram bot
- **Email** — SMTP email (Gmail App Password recommended)

### Telegram Setup
1. Open Telegram, search for `@BotFather`
2. Send `/newbot` and follow the prompts to get your `TELEGRAM_BOT_TOKEN`
3. Get your `TELEGRAM_CHAT_ID` by messaging `@userinfobot`

### Gmail App Password
1. Enable 2-factor auth on your Google account
2. Go to Google Account → Security → App Passwords
3. Generate a password for "Mail" and use it as `SMTP_PASSWORD`

## Running Tests

```bash
python -m pytest tests/ -v
```
