# Credentials Setup

## What The User Must Provide

For live trading, collect these separately:

- wallet private key for signing
- funder address if funds live outside the signer EOA
- API key, API secret, and API passphrase if already provisioned

An API key alone is not enough for authenticated trading calls.

## Suggested Environment Variables

```bash
export POLYMARKET_HOST="https://clob.polymarket.com"
export POLYMARKET_CHAIN_ID="137"
export POLYMARKET_SIGNATURE_TYPE="0"

export POLYMARKET_PRIVATE_KEY="0x..."
export POLYMARKET_FUNDER="0x..."

export POLYMARKET_API_KEY="..."
export POLYMARKET_API_SECRET="..."
export POLYMARKET_API_PASSPHRASE="..."
```

## Safe Defaults

- Keep credentials in shell environment or a local untracked env file.
- Do not write real secrets into the skill folder.
- Run `trade.py healthcheck` before trying balances or orders.
- If API secret or passphrase is missing but private key exists, derive creds instead of guessing.
