---
name: polymarket-trading
description: "Read Polymarket market data, inspect bridge/funding options, and place or review CLOB orders using Polymarket's official APIs and clients. Use when Codex needs to fetch markets, events, prices, or order books; prepare deposits or withdrawals through the official bridge; derive API credentials; inspect balances or open orders; or submit Polymarket trades safely with explicit confirmation."
---

# Polymarket Trading

## Overview

Use official Polymarket endpoints for read-only queries and prefer the official Python CLOB client for authenticated trading flows.

This skill is execution and inspection oriented. It should not decide which side is "good" or make directional trading decisions for the user. Its job is to surface the market rules, prices, liquidity, token IDs, restrictions, and execution status clearly enough for the user to choose.

## Workflow

1. Classify the request as one of:
- Read-only market data
- Bridge funding or withdrawal
- Authenticated CLOB trading

For authenticated CLOB trading on a machine with Mihomo or Clash-style VPN, the default sequence is:
1. Run `scripts/trade.py healthcheck`.
2. If geography may block trading, run `scripts/vpn_helper.py geoblock`.
3. If `geoblock` fails or reports a blocked exit, use `scripts/vpn_helper.py groups` and `select` to switch to an allowed region.
4. Re-run `scripts/vpn_helper.py geoblock` until it succeeds.
5. Export `HTTP_PROXY`, `HTTPS_PROXY`, and `ALL_PROXY` for all authenticated trade commands.
6. Only then check balances, create the order, and submit it.

2. Load only the references you need:
- Read [references/api-surfaces.md](./references/api-surfaces.md) for endpoint selection and surface boundaries.
- Read [references/trading-checklist.md](./references/trading-checklist.md) before any live order or funding action.
- Read [references/credentials-setup.md](./references/credentials-setup.md) when the user gives partial credentials or wallet details.
- Read [references/vpn-coordination.md](./references/vpn-coordination.md) when the machine uses a local proxy or Mihomo/Clash-style VPN and Polymarket may geoblock the current exit.

3. Use the bundled scripts first:
- `scripts/market_info.py` for markets, events, and prices
- `scripts/bridge.py` for supported assets, deposit addresses, quotes, withdrawal addresses, and status polling
- `scripts/trade.py` for credential derivation, balances, open orders, and limit-order creation/submission
- `scripts/vpn_helper.py` for Mihomo selector inspection, node switching, proxied IP checks, and Polymarket geoblock checks
- `scripts/trade_with_vpn.py` to auto-check geoblock, optionally switch Mihomo nodes, inject proxy env vars, and then run `trade.py`
- Start trading sessions with `scripts/trade.py healthcheck` to confirm host reachability and which credential pieces are still missing.

4. Treat anything that moves funds or submits an order as high risk:
- Confirm the exact market, token ID, side, size, and price.
- Confirm whether the user wants a dry run or a live submission.
- Before any live order, surface the market description and any unusual resolution logic such as `50-50` fallback, multi-trigger conditions, void paths, or special settlement clauses.
- Do not describe Polymarket as generic fiat "payment". Model funding as deposit/withdraw of assets bridged into or out of the Polymarket wallet.

## Runtime Guidance

- Prefer `uv run --python 3.11` for these scripts. The current machine may have an older default `python3`.
- For read-only commands, inject only `requests`.
- For trading commands, inject `py-clob-client`.
- When Polymarket geoblocks the machine, switch the Mihomo selector to an allowed region, verify `blocked: false` through the proxy, then export `HTTP_PROXY`, `HTTPS_PROXY`, and `ALL_PROXY` before authenticated trading calls.
- Treat `scripts/vpn_helper.py geoblock` as a gate: if it exits non-zero, do not submit the order yet.
- Keep secrets in environment variables, never inline in prompts or committed files.

Example commands:

```bash
uv run --python 3.11 --with requests scripts/market_info.py markets --query "fed" --limit 5
uv run --python 3.11 --with requests scripts/bridge.py supported-assets
uv run --python 3.11 --with py-clob-client scripts/trade.py healthcheck
uv run --python 3.11 --with py-clob-client scripts/trade.py derive-creds
uv run --python 3.11 --with requests scripts/vpn_helper.py groups
uv run --python 3.11 --with requests scripts/vpn_helper.py select --group "良心云" --proxy "🇭🇰香港高速01|BGP|流媒体"
uv run --python 3.11 --with requests scripts/vpn_helper.py geoblock
uv run --python 3.11 --with py-clob-client scripts/trade_with_vpn.py --proxy "🇭🇰香港高速01|BGP|流媒体" -- balance --asset-type collateral
```

## Read-Only Queries

- Use Gamma for market and event discovery.
- Use CLOB pricing endpoints for token-level price checks.
- Summarize the returned market question, slug, active/closed state, liquidity, end date, outcome prices, and the important parts of the resolution rules when present.
- Do not turn that summary into a recommendation unless the user explicitly asks for analysis. Even then, keep decision ownership with the user and highlight rule-driven caveats first.
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
- Before posting a live order, show the user the relevant resolution-rule caveats from the market description instead of assuming the market is a standard binary contract.
- Explain the wallet roles clearly:
  - signer/private key: the key that signs authentication and orders
  - funder: the address that actually holds USDC.e or conditional tokens
- Check geography and Cloudflare restrictions before assuming a failed order is an application bug.
- If the machine has a local Mihomo controller and mixed proxy, prefer using `scripts/vpn_helper.py` to switch to an allowed region and route the authenticated trade calls through that proxy.
- For routine live trading on a Mihomo-backed machine, prefer `scripts/trade_with_vpn.py` over manual environment exports. It should be the default wrapper when the agent needs to trade through the local proxy.
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
- When VPN coordination fails, report the exact failing step, the controller or proxy endpoint involved, and the suggested next action from the script output.
- When a market has unusual resolution logic, call it out explicitly as a caution, not as a reason to automatically reject or choose a side.
