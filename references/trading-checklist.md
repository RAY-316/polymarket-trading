# Trading Checklist

## Before Any Live Order

1. Confirm the request is for a real trade, not just price discovery.
2. Confirm market question, outcome, and `token_id`.
3. Confirm side, price, size, and order type.
4. Confirm whether to dry run or submit.
5. Confirm the user understands geographic restrictions and wallet risk.

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

## Funding Notes

- Deposits bridge supported assets into `USDC.e` on Polygon.
- Withdrawals move `USDC.e` out to a supported destination chain/token.
- Use bridge quotes before execution.
- Do not pre-generate withdrawal addresses unless the user is about to execute the withdrawal.

## Safe Execution Pattern

1. Run a read-only market query.
2. Fetch price data.
3. Check balances or allowances.
4. Create the order locally.
5. Submit only with explicit live intent.
