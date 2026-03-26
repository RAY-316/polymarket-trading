#!/usr/bin/env python3
import argparse
import json
import os
import sys


def require_client():
    try:
        from py_clob_client.client import ClobClient
        from py_clob_client.clob_types import (
            ApiCreds,
            BalanceAllowanceParams,
            MarketOrderArgs,
            OpenOrderParams,
            OrderArgs,
        )
        from py_clob_client.order_builder.constants import BUY, SELL
        from py_clob_client.clob_types import AssetType
    except ImportError:
        raise SystemExit(
            "Missing py-clob-client. Run with: "
            "uv run --python 3.11 --with py-clob-client scripts/trade.py ..."
        )
    return {
        "ClobClient": ClobClient,
        "ApiCreds": ApiCreds,
        "BalanceAllowanceParams": BalanceAllowanceParams,
        "MarketOrderArgs": MarketOrderArgs,
        "OpenOrderParams": OpenOrderParams,
        "OrderArgs": OrderArgs,
        "BUY": BUY,
        "SELL": SELL,
        "AssetType": AssetType,
    }


def dump(data):
    print(json.dumps(data, indent=2, sort_keys=True, default=str))


def has_value(name):
    value = os.getenv(name)
    return bool(value and value.strip())


def env_int(name, default):
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def build_client(with_auth):
    exports = require_client()
    host = os.getenv("POLYMARKET_HOST", "https://clob.polymarket.com")
    chain_id = env_int("POLYMARKET_CHAIN_ID", 137)
    private_key = os.getenv("POLYMARKET_PRIVATE_KEY")
    signature_type = env_int("POLYMARKET_SIGNATURE_TYPE", 0)
    funder = os.getenv("POLYMARKET_FUNDER")

    if not private_key:
        raise SystemExit("Set POLYMARKET_PRIVATE_KEY in the environment.")

    client = exports["ClobClient"](
        host,
        chain_id=chain_id,
        key=private_key,
        signature_type=signature_type,
        funder=funder,
    )

    if with_auth:
        api_key = os.getenv("POLYMARKET_API_KEY")
        api_secret = os.getenv("POLYMARKET_API_SECRET")
        api_passphrase = os.getenv("POLYMARKET_API_PASSPHRASE")
        if api_key and api_secret and api_passphrase:
            creds = exports["ApiCreds"](
                api_key=api_key,
                api_secret=api_secret,
                api_passphrase=api_passphrase,
            )
        else:
            creds = client.create_or_derive_api_creds()
        client.set_api_creds(creds)
        return client, exports, creds

    return client, exports, None


def cmd_healthcheck(_args):
    import requests

    host = os.getenv("POLYMARKET_HOST", "https://clob.polymarket.com")
    chain_id = env_int("POLYMARKET_CHAIN_ID", 137)
    checks = {
        "host": host,
        "chain_id": chain_id,
        "has_private_key": has_value("POLYMARKET_PRIVATE_KEY"),
        "has_funder": has_value("POLYMARKET_FUNDER"),
        "has_api_key": has_value("POLYMARKET_API_KEY"),
        "has_api_secret": has_value("POLYMARKET_API_SECRET"),
        "has_api_passphrase": has_value("POLYMARKET_API_PASSPHRASE"),
        "signature_type": env_int("POLYMARKET_SIGNATURE_TYPE", 0),
    }
    try:
        response = requests.get("%s/time" % host, timeout=20)
        checks["public_http_status"] = response.status_code
        checks["public_time"] = response.json()
    except Exception as exc:
        checks["public_http_error"] = str(exc)
    dump(checks)


def cmd_derive_creds(_args):
    client, _exports, creds = build_client(with_auth=True)
    dump(
        {
            "host": os.getenv("POLYMARKET_HOST", "https://clob.polymarket.com"),
            "funder": os.getenv("POLYMARKET_FUNDER"),
            "creds": {
                "api_key": creds.api_key,
                "api_secret": creds.api_secret,
                "api_passphrase": creds.api_passphrase,
            },
        }
    )


def cmd_balance(args):
    client, exports, _creds = build_client(with_auth=True)
    asset_type = (
        exports["AssetType"].COLLATERAL
        if args.asset_type == "collateral"
        else exports["AssetType"].CONDITIONAL
    )
    params = {"asset_type": asset_type, "signature_type": env_int("POLYMARKET_SIGNATURE_TYPE", 0)}
    if args.token_id:
        params["token_id"] = args.token_id
    result = client.get_balance_allowance(exports["BalanceAllowanceParams"](**params))
    dump(result)


def cmd_approve(args):
    client, exports, _creds = build_client(with_auth=True)
    asset_type = (
        exports["AssetType"].COLLATERAL
        if args.asset_type == "collateral"
        else exports["AssetType"].CONDITIONAL
    )
    params = {"asset_type": asset_type, "signature_type": env_int("POLYMARKET_SIGNATURE_TYPE", 0)}
    if args.token_id:
        params["token_id"] = args.token_id
    result = client.update_balance_allowance(exports["BalanceAllowanceParams"](**params))
    dump(result)


def cmd_orders(args):
    client, exports, _creds = build_client(with_auth=True)
    params = {}
    if args.order_id:
        params["id"] = args.order_id
    if args.market:
        params["market"] = args.market
    if args.asset_id:
        params["asset_id"] = args.asset_id
    if params:
        result = client.get_orders(exports["OpenOrderParams"](**params))
    else:
        result = client.get_orders()
    dump(result)


def cmd_get_order(args):
    client, _exports, _creds = build_client(with_auth=True)
    dump(client.get_order(args.order_id))


def cmd_cancel_orders(args):
    client, _exports, _creds = build_client(with_auth=True)
    if args.all:
        result = client.cancel_all()
    elif args.market:
        result = client.cancel_market_orders(market=args.market, asset_id=args.asset_id or "")
    else:
        if not args.order_id:
            raise SystemExit("Provide --order-id, --market, or --all.")
        result = client.cancel_orders(args.order_id)
    dump(result)


def cmd_limit_order(args):
    client, exports, _creds = build_client(with_auth=True)
    side = exports["BUY"] if args.side == "buy" else exports["SELL"]
    order = client.create_order(
        exports["OrderArgs"](
            token_id=args.token_id,
            price=args.price,
            size=args.size,
            side=side,
        )
    )
    if args.submit:
        result = client.post_order(
            order,
            orderType=args.order_type.upper(),
            post_only=args.post_only,
        )
        dump({"submitted": True, "response": result})
    else:
        dump({"submitted": False, "signed_order": order})


def cmd_market_order(args):
    client, exports, _creds = build_client(with_auth=True)
    side = exports["BUY"] if args.side == "buy" else exports["SELL"]
    order = client.create_market_order(
        exports["MarketOrderArgs"](
            token_id=args.token_id,
            amount=args.amount,
            side=side,
            price=args.price,
        )
    )
    if args.submit:
        result = client.post_order(order, orderType=args.order_type.upper())
        dump({"submitted": True, "response": result})
    else:
        dump({"submitted": False, "signed_order": order})


def build_parser():
    parser = argparse.ArgumentParser(description="Inspect or place Polymarket CLOB orders.")
    sub = parser.add_subparsers(dest="command")
    sub.required = True

    healthcheck = sub.add_parser("healthcheck", help="Check public connectivity and credential presence.")
    healthcheck.set_defaults(func=cmd_healthcheck)

    derive_creds = sub.add_parser("derive-creds", help="Create or derive API credentials.")
    derive_creds.set_defaults(func=cmd_derive_creds)

    balance = sub.add_parser("balance", help="Check balance and allowance.")
    balance.add_argument("--asset-type", choices=["collateral", "conditional"], default="collateral")
    balance.add_argument("--token-id", help="Required for conditional token checks.")
    balance.set_defaults(func=cmd_balance)

    approve = sub.add_parser("approve", help="Update allowance for collateral or conditional tokens.")
    approve.add_argument("--asset-type", choices=["collateral", "conditional"], default="collateral")
    approve.add_argument("--token-id", help="Required for conditional token approvals.")
    approve.set_defaults(func=cmd_approve)

    orders = sub.add_parser("orders", help="List open orders or filter them.")
    orders.add_argument("--order-id")
    orders.add_argument("--market")
    orders.add_argument("--asset-id")
    orders.set_defaults(func=cmd_orders)

    get_order = sub.add_parser("get-order", help="Fetch one order by id.")
    get_order.add_argument("--order-id", required=True)
    get_order.set_defaults(func=cmd_get_order)

    cancel_orders = sub.add_parser("cancel", help="Cancel specific orders, a market, or everything.")
    cancel_orders.add_argument("--order-id", nargs="+", help="One or more order ids.")
    cancel_orders.add_argument("--market", help="Cancel all open orders in one market.")
    cancel_orders.add_argument("--asset-id", help="Optional asset id filter when canceling a market.")
    cancel_orders.add_argument("--all", action="store_true", help="Cancel all open orders.")
    cancel_orders.set_defaults(func=cmd_cancel_orders)

    limit_order = sub.add_parser("limit-order", help="Create a signed limit order and optionally submit it.")
    limit_order.add_argument("--token-id", required=True)
    limit_order.add_argument("--side", choices=["buy", "sell"], required=True)
    limit_order.add_argument("--price", type=float, required=True)
    limit_order.add_argument("--size", type=float, required=True)
    limit_order.add_argument("--order-type", choices=["gtc", "gtd", "fok", "fak"], default="gtc")
    limit_order.add_argument("--post-only", action="store_true")
    limit_order.add_argument("--submit", action="store_true", help="Actually post the order.")
    limit_order.set_defaults(func=cmd_limit_order)

    market_order = sub.add_parser("market-order", help="Create a signed market-style order and optionally submit it.")
    market_order.add_argument("--token-id", required=True)
    market_order.add_argument("--side", choices=["buy", "sell"], required=True)
    market_order.add_argument("--amount", type=float, required=True, help="Collateral amount for BUY or token amount for SELL.")
    market_order.add_argument("--price", type=float, required=True, help="Worst acceptable execution price.")
    market_order.add_argument("--order-type", choices=["fok", "fak"], default="fok")
    market_order.add_argument("--submit", action="store_true")
    market_order.set_defaults(func=cmd_market_order)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
