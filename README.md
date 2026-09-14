# DeFi Alert Bot

Telegram bot that monitors DeFi yield opportunities, filters pools by liquidity/APY rules, detects new opportunities and APY jumps, and delivers scheduled alerts to subscribers.

The project combines **Telegram automation, external financial-data APIs, scheduled jobs, state snapshots and a subscription checkout flow**.

> Portfolio / educational project. Nothing produced by this bot should be considered financial advice.

## What it does

- Pulls yield-pool data from the DeFiLlama API.
- Filters opportunities by protocol, APY and TVL thresholds.
- Ranks pools by APY.
- Detects new pools entering the monitored set.
- Detects significant APY changes against the previous snapshot.
- Sends recurring alerts and a daily digest through Telegram.
- Provides `/start`, `/top`, `/alerts` and `/help` commands.
- Restricts premium features to active subscribers.
- Creates Stripe Checkout sessions through a small FastAPI service.

## High-level architecture

```text
                    DeFiLlama API
                         |
                         v
                 +----------------+
                 | pool filtering |
                 | + ranking      |
                 +----------------+
                         |
               snapshot comparison
                         |
           +-------------+-------------+
           |                           |
           v                           v
   Telegram commands          scheduled jobs
   /top /alerts               alerts + digest
           |                           |
           +-------------+-------------+
                         |
                         v
                    subscribers

Telegram user -- premium gate --> Checkout API --> Stripe Checkout
```

## Project structure

```text
defi-alert-bot/
├── bot_unificado.py        # Telegram application + scheduled jobs
├── config.py               # Environment-driven configuration
├── stripe_api.py           # FastAPI endpoint for Stripe Checkout
├── modules/
│   └── handlers.py         # Commands, callbacks and alert delivery
├── services/
│   └── defillama.py        # DeFiLlama integration + pool filters
├── storage/
│   ├── users.py
│   ├── subscribers.py
│   └── defi_alerts.py      # Snapshot persistence/comparison
├── requirements.txt
└── .env.example
```

## Stack

- Python
- python-telegram-bot
- FastAPI
- Stripe Checkout
- DeFiLlama API
- Requests
- scheduled/background jobs
- JSON-based local persistence for the MVP

## Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Main variables:

```env
TELEGRAM_TOKEN=
ADMIN_USER_IDS=

DEFI_TOP_LIMIT=5
DEFI_APY_MIN=10
DEFI_APY_MAX=200
DEFI_TVL_MIN=1000000
APY_JUMP_MIN=10
ALERT_CHECK_MINUTES=15
DEFI_DIGEST_HOUR=9
DEFI_DIGEST_MINUTE=0

CHECKOUT_API_URL=http://localhost:8000
STRIPE_SECRET_KEY=
STRIPE_PRICE_ID=
```

## Running locally

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

Start the checkout API:

```bash
uvicorn stripe_api:app --host 0.0.0.0 --port 8000
```

Then start the Telegram bot:

```bash
python bot_unificado.py
```

## Filtering logic

The DeFiLlama service layer:

1. fetches current pools;
2. validates required fields;
3. keeps selected/allowlisted protocols;
4. applies minimum/maximum APY and minimum TVL thresholds;
5. sorts the remaining pools by APY;
6. returns the configured top set.

The alert layer compares that result with the previous stored snapshot to identify new entries and strong APY jumps.

## Subscription flow

Premium commands check whether the Telegram user is registered as an active subscriber. If not, the bot requests a checkout URL from the FastAPI service, which creates a Stripe Checkout subscription session with Telegram identifiers stored as metadata.

The repository demonstrates the checkout/session side of the flow. A complete production billing setup should also reconcile Stripe webhook events before granting or revoking access.

## MVP trade-offs

This project intentionally keeps storage simple for the MVP. User, subscriber and snapshot state are persisted locally as JSON files and excluded from version control.

For a production version, I would move subscription/user state to a transactional database and add a complete Stripe webhook/reconciliation flow.

## Author

**Karlos Sanchez** — Full-Stack Developer focused on automation, integrations and business systems.

[LinkedIn](https://www.linkedin.com/in/karlos-sanchez/) · [GitHub profile](https://github.com/KarlosSanchez18)
