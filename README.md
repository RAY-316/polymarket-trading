# Polymarket Trading Skill

Codex skill for Polymarket market discovery, bridge funding, and CLOB trading.

## Contents

- `SKILL.md`: skill instructions and workflow
- `scripts/market_info.py`: market, event, and price queries
- `scripts/bridge.py`: bridge supported assets, quotes, deposits, withdrawals, status
- `scripts/trade.py`: healthcheck, derive creds, balances, approvals, order management, order creation
- `references/`: API surface, credentials, and trading safety notes

## Install Location

This repository is designed so the repository root is the skill root. Cloning it under a skills directory works directly:

```bash
git clone https://github.com/RAY-316/polymarket-trading.git ~/.openclaw/workspace/skills/polymarket-trading
```

## Environment Configuration

The scripts read standard environment variables:

```bash
export POLYMARKET_PRIVATE_KEY="0x..."
export POLYMARKET_FUNDER="0x..."
export POLYMARKET_CHAIN_ID="137"
export POLYMARKET_SIGNATURE_TYPE="0"
export POLYMARKET_HOST="https://clob.polymarket.com"
```

Optional:

```bash
export POLYMARKET_API_KEY="..."
export POLYMARKET_API_SECRET="..."
export POLYMARKET_API_PASSPHRASE="..."
```

Recommended local setup:

1. Copy `.env.example` to a local untracked env file such as `~/.config/polymarket.env`
2. Fill in your real values
3. Use `./polymarket-skill` or `source ~/.config/polymarket.env` before running scripts

## Local Launcher

The repository includes `./polymarket-skill`, which sources `~/.config/polymarket.env` by default.

Examples:

```bash
./polymarket-skill trade healthcheck
./polymarket-skill trade derive-creds
./polymarket-skill trade balance
./polymarket-skill market markets --query "trump" --limit 5
./polymarket-skill bridge supported-assets
```

Override the env file path with:

```bash
POLYMARKET_ENV_FILE=/path/to/your.env ./polymarket-skill trade healthcheck
```

## Safety

- Do not commit real secrets.
- Do not store live private keys in tracked files.
- If a private key has been exposed, rotate it before funding the wallet.
