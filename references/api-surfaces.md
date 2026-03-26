# Polymarket API Surfaces

## Overview

Use the official Polymarket surfaces according to the task:

- Gamma API: market and event discovery
- CLOB API: prices, books, auth, balances, orders
- Bridge API: deposits, withdrawals, quotes, status

Primary docs:

- `https://docs.polymarket.com/api-reference/markets/list-markets`
- `https://docs.polymarket.com/api-reference/pricing/get-market-price`
- `https://docs.polymarket.com/api-reference/authentication`
- `https://docs.polymarket.com/api-reference/bridge/get-supported-assets`
- `https://docs.polymarket.com/api-reference/bridge/get-a-quote`
- `https://docs.polymarket.com/api-reference/bridge/create-deposit-addresses`
- `https://docs.polymarket.com/api-reference/bridge/create-withdrawal-addresses`
- `https://docs.polymarket.com/api-reference/bridge/get-transaction-status`

## Base URLs

- Gamma: `https://gamma-api.polymarket.com`
- CLOB: `https://clob.polymarket.com`
- Bridge: `https://bridge.polymarket.com`

## Recommended Mapping

### Discovery

Use Gamma endpoints for:

- listing markets
- searching by question text or slug
- listing events
- reading market metadata such as question, category, liquidity, end date, outcomes

### Pricing

Use CLOB pricing for:

- token-level price snapshots
- order-book-aware checks before trading

### Trading

Prefer official clients over hand-built signatures for:

- deriving API credentials
- checking balances and allowances
- creating signed orders
- posting and canceling orders

### Funding

Use Bridge API for:

- `GET /supported-assets`
- `POST /quote`
- `POST /deposit`
- `POST /withdraw`
- `GET /status/{address}`

## Constraints To Respect

- Funding is asset bridging into or out of the Polymarket wallet, not generic card charging.
- Trading may fail because of restricted geography, Cloudflare checks, missing wallet deployment, missing balances, or missing allowances.
- All trading collateral is `USDC.e` on Polygon according to the bridge and getting-started docs.
- Read-only endpoints can be used without private keys; trading endpoints cannot.
