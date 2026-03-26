# VPN Coordination

Use this reference when Polymarket trading depends on a local Mihomo or Clash-style proxy.

## When To Use

- `trade.py healthcheck` or an order submission shows `Trading restricted in your region`
- The machine has a Mihomo REST controller, usually `http://127.0.0.1:9090`
- The machine has a local mixed proxy, usually `http://127.0.0.1:7890`

## Preferred Flow

1. Inspect selector groups:

```bash
uv run --python 3.11 --with requests scripts/vpn_helper.py groups
```

2. Switch the main selector to an allowed region, for example Hong Kong:

```bash
uv run --python 3.11 --with requests scripts/vpn_helper.py select --group "良心云" --proxy "🇭🇰香港高速01|BGP|流媒体"
```

3. Verify the proxied IP and Polymarket geoblock result:

```bash
uv run --python 3.11 --with requests scripts/vpn_helper.py ip
uv run --python 3.11 --with requests scripts/vpn_helper.py geoblock
```

If `geoblock` exits non-zero, treat that as a hard stop for live trading. Fix the exit region first.

4. Only when `geoblock.blocked` is `false`, route authenticated trade calls through the local proxy:

```bash
export HTTP_PROXY="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"
export ALL_PROXY="http://127.0.0.1:7890"
uv run --python 3.11 --with py-clob-client scripts/trade.py balance --asset-type collateral
```

Or use the wrapper that does this for you:

```bash
uv run --python 3.11 --with py-clob-client scripts/trade_with_vpn.py --proxy "🇭🇰香港高速01|BGP|流媒体" -- balance --asset-type collateral
```

For live orders:

```bash
uv run --python 3.11 --with py-clob-client scripts/trade_with_vpn.py \
  --proxy "🇭🇰香港高速01|BGP|流媒体" \
  -- market-order --token-id 123 --side buy --amount 5 --price 0.52 --order-type fak --submit
```

## Notes

- `geoblock` must be checked through the proxy, not just from the machine's default network path.
- A successful public `healthcheck` is not enough; order submission can still fail with `403` if the authenticated request leaves through a blocked exit.
- The Mihomo controller and proxy addresses can be overridden with `MIHOMO_CONTROLLER` and `MIHOMO_PROXY`.
- `vpn_helper.py` is opinionated on purpose: it returns non-zero with a clear JSON error when the controller is down, the selected proxy is missing, the local proxy is unreachable, or Polymarket still reports `blocked: true`.
