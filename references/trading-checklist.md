# Trading Checklist

## Before Any Live Order

1. Confirm the request is for a real trade, not just price discovery.
2. Confirm market question, outcome, and `token_id`.
3. Read the market description and surface any special resolution logic before the order.
4. Confirm side, price, size, and order type.
5. Confirm whether to dry run or submit.
6. Confirm the user understands geographic restrictions, market rules, and wallet risk.
7. If a local proxy or Mihomo controller exists, verify the proxied `https://polymarket.com/api/geoblock` result before posting the order.

## Credentials And Wallet Shape

- Signer key signs auth and orders.
- Funder address holds collateral or outcome tokens.
- `signature_type=0` usually means direct EOA.
- Proxy or Safe-style setups can require different signature types and a distinct funder address.

## Common Failure Modes

- `invalid api key`: derive or create API creds again and attach them to the client.
- `insufficient balance`: check the funder wallet, not just the signer.
- `insufficient allowance`: approve the exchange or CTF path first.
- Cloudflare/geoblock: treat as an environment restriction, not a code bug.
- Local proxy not applied: authenticated calls can still hit the machine's default exit unless `HTTP_PROXY`, `HTTPS_PROXY`, and `ALL_PROXY` are exported for the trade command.

## Funding Notes

- Deposits bridge supported assets into `USDC.e` on Polygon.
- Withdrawals move `USDC.e` out to a supported destination chain/token.
- Use bridge quotes before execution.
- Do not pre-generate withdrawal addresses unless the user is about to execute the withdrawal.

## Safe Execution Pattern

1. Run a read-only market query.
2. Read the market rules and point out any unusual settlement clauses.
3. If needed, switch the local proxy to an allowed region and verify `blocked: false`.
4. Fetch price data.
5. Check balances or allowances.
6. Create the order locally.
7. Submit only with explicit live intent.
