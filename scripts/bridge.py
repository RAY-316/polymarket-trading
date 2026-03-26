#!/usr/bin/env python3
import argparse
import json
import sys

import requests


BRIDGE_BASE = "https://bridge.polymarket.com"


def dump(data):
    print(json.dumps(data, indent=2, sort_keys=True))


def get_json(path):
    response = requests.get("%s%s" % (BRIDGE_BASE, path), timeout=30)
    response.raise_for_status()
    return response.json()


def post_json(path, payload):
    response = requests.post(
        "%s%s" % (BRIDGE_BASE, path),
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def cmd_supported_assets(_args):
    dump(get_json("/supported-assets"))


def cmd_deposit(args):
    dump(post_json("/deposit", {"address": args.address}))


def cmd_quote(args):
    payload = {
        "fromAmountBaseUnit": args.from_amount_base_unit,
        "fromChainId": args.from_chain_id,
        "fromTokenAddress": args.from_token_address,
        "recipientAddress": args.recipient_address,
        "toChainId": args.to_chain_id,
        "toTokenAddress": args.to_token_address,
    }
    dump(post_json("/quote", payload))


def cmd_status(args):
    dump(get_json("/status/%s" % args.address))


def cmd_withdraw(args):
    payload = {
        "address": args.address,
        "toChainId": args.to_chain_id,
        "toTokenAddress": args.to_token_address,
        "recipientAddr": args.recipient_addr,
    }
    dump(post_json("/withdraw", payload))


def build_parser():
    parser = argparse.ArgumentParser(description="Use Polymarket bridge endpoints.")
    sub = parser.add_subparsers(dest="command")
    sub.required = True

    supported_assets = sub.add_parser("supported-assets", help="List supported bridge assets.")
    supported_assets.set_defaults(func=cmd_supported_assets)

    deposit = sub.add_parser("deposit", help="Create deposit addresses for a Polymarket wallet.")
    deposit.add_argument("--address", required=True, help="Polymarket wallet address on Polygon.")
    deposit.set_defaults(func=cmd_deposit)

    quote = sub.add_parser("quote", help="Request a bridge quote.")
    quote.add_argument("--from-amount-base-unit", required=True)
    quote.add_argument("--from-chain-id", required=True)
    quote.add_argument("--from-token-address", required=True)
    quote.add_argument("--recipient-address", required=True)
    quote.add_argument("--to-chain-id", required=True)
    quote.add_argument("--to-token-address", required=True)
    quote.set_defaults(func=cmd_quote)

    status = sub.add_parser("status", help="Poll transaction status for a deposit or withdrawal address.")
    status.add_argument("--address", required=True)
    status.set_defaults(func=cmd_status)

    withdraw = sub.add_parser("withdraw", help="Create withdrawal addresses for a Polymarket wallet.")
    withdraw.add_argument("--address", required=True, help="Source Polymarket wallet address.")
    withdraw.add_argument("--to-chain-id", required=True)
    withdraw.add_argument("--to-token-address", required=True)
    withdraw.add_argument("--recipient-addr", required=True)
    withdraw.set_defaults(func=cmd_withdraw)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except requests.HTTPError as exc:
        body = exc.response.text if exc.response is not None else str(exc)
        print(body, file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
