---
name: polymarket-trading
description: "Read Polymarket market data, inspect bridge/funding options, and place or review CLOB orders using Polymarket's official APIs and clients. Use when Codex needs to fetch markets, events, prices, or order books; prepare deposits or withdrawals through the official bridge; derive API credentials; inspect balances or open orders; or submit Polymarket trades safely with explicit confirmation."
---

# Polymarket Trading

## Overview

Use official Polymarket endpoints for read-only queries and prefer the official Python CLOB client for authenticated trading flows.

## Workflow

1. Classify the request as one of:
- Read-only market data
- Bridge funding or withdrawal
- Authenticated CLOB trading

2. Load only the references you need:
- Read [references/api-surfaces.md](./references/api-surfaces.md) for endpoint selection and surface boundaries.
- Read [references/trading-checklist.md](./references/trading-checklist.md) before any live order or funding action.
- Read [references/credentials-setup.md](./references/credentials-setup.md) when the user gives partial credentials or wallet details.

3. Use the bundled scripts first:
- `scripts/market_info.py` for markets, events, and prices
- `scripts/bridge.py` for supported assets, deposit addresses, quotes, withdrawal addresses, and status polling
- `scripts/trade.py` for credential derivation, balances, open orders, and limit-order creation/submission
- Start trading sessions with `scripts/trade.py healthcheck` to confirm host reachability and which credential pieces are still missing.

4. Treat anything that moves funds or submits an order as high risk:
- Confirm the exact market, token ID, side, size, and price.
- Confirm whether the user wants a dry run or a live submission.
- Do not describe Polymarket as generic fiat "payment". Model funding as deposit/withdraw of assets bridged into or out of the Polymarket wallet.

## Runtime Guidance

- Prefer `uv run --python 3.11` for these scripts. The current machine may have an older default `python3`.
- For read-only commands, inject only `requests`.
- For trading commands, inject `py-clob-client`.
- Keep secrets in environment variables, never inline in prompts or committed files.

Example commands:

```bash
uv run --python 3.11 --with requests scripts/market_info.py markets --query "fed" --limit 5
uv run --python 3.11 --with requests scripts/bridge.py supported-assets
uv run --python 3.11 --with py-clob-client scripts/trade.py healthcheck
uv run --python 3.11 --with py-clob-client scripts/trade.py derive-creds
```

## Read-Only Queries

- Use Gamma for market and event discovery.
- Use CLOB pricing endpoints for token-level price checks.
- Summarize the returned market question, slug, active/closed state, liquidity, end date, and outcome prices when present.
- If the user asks for "latest" market information, fetch it live rather than relying on memory.

## Funding And Withdrawal

- Use the bridge API for cross-chain deposits into the Polymarket wallet.
- Use `/supported-assets` before quoting, depositing, or withdrawing.
- Use `/quote` to preview route costs and amounts.
- Use `/deposit` to generate inbound bridge addresses for the user's Polymarket wallet.
- Use `/withdraw` only when the user is ready to execute. Do not pre-generate withdrawal addresses casually.
- Use `/status/{address}` to track bridge progress after funds are sent.

## Trading

- Prefer the official `py-clob-client` for order creation and authenticated requests.
- Derive or create API credentials from the signing key, then attach them to the client before requesting balances or posting orders.
- If the user provides only an API key or only a wallet address, treat that as incomplete and ask for or derive the missing pieces instead of guessing.
- Explain the wallet roles clearly:
  - signer/private key: the key that signs authentication and orders
  - funder: the address that actually holds USDC.e or conditional tokens
- Check geography and Cloudflare restrictions before assuming a failed order is an application bug.
- Check balances and allowances before blaming order parameters.
- For BUY orders, expect USDC.e in the funder address.
- For SELL orders, expect the outcome token in the funder address.

## Required Environment Variables For Trading

- `POLYMARKET_PRIVATE_KEY`: signer private key
- `POLYMARKET_FUNDER`: funder wallet address when funds are held outside the signer EOA
- `POLYMARKET_SIGNATURE_TYPE`: default `0`; use the user's actual wallet type if different
- `POLYMARKET_HOST`: defaults to `https://clob.polymarket.com`
- `POLYMARKET_CHAIN_ID`: defaults to `137`
- `POLYMARKET_API_KEY`, `POLYMARKET_API_SECRET`, `POLYMARKET_API_PASSPHRASE`: optional if already provisioned; otherwise derive them

## Output Expectations

- For read-only work, return concise structured summaries plus raw JSON when useful.
- For bridge and order preparation, show the exact command and payload before any live action.
- For live actions, report the official response body and the next verification step.
