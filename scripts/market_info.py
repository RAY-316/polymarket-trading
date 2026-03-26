#!/usr/bin/env python3
import argparse
import json
import sys

import requests


GAMMA_BASE = "https://gamma-api.polymarket.com"
CLOB_BASE = "https://clob.polymarket.com"


def dump(data):
    print(json.dumps(data, indent=2, sort_keys=True))


def get_json(url, params=None):
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def shortlist_markets(markets, query, slug, market_id, limit):
    items = markets
    if market_id:
        items = [m for m in items if str(m.get("id")) == market_id]
    if slug:
        items = [m for m in items if m.get("slug") == slug]
    if query:
        needle = query.lower()
        items = [
            m
            for m in items
            if needle in (m.get("question") or "").lower()
            or needle in (m.get("slug") or "").lower()
        ]
    return items[:limit]


def cmd_markets(args):
    fetch_limit = max(args.limit * 5, 50)
    params = {
        "limit": fetch_limit,
        "closed": str(args.closed).lower(),
        "archived": str(args.archived).lower(),
    }
    data = get_json("%s/markets" % GAMMA_BASE, params=params)
    items = shortlist_markets(data, args.query, args.slug, args.market_id, args.limit)
    summary = []
    for market in items:
        summary.append(
            {
                "id": market.get("id"),
                "slug": market.get("slug"),
                "question": market.get("question"),
                "description": market.get("description"),
                "resolutionSource": market.get("resolutionSource"),
                "active": market.get("active"),
                "closed": market.get("closed"),
                "liquidity": market.get("liquidity"),
                "endDate": market.get("endDate"),
                "outcomes": market.get("outcomes"),
                "outcomePrices": market.get("outcomePrices"),
            }
        )
    dump(summary)


def cmd_events(args):
    params = {"limit": args.limit}
    data = get_json("%s/events" % GAMMA_BASE, params=params)
    if args.query:
        needle = args.query.lower()
        data = [
            event
            for event in data
            if needle in (event.get("title") or "").lower()
            or needle in (event.get("slug") or "").lower()
        ]
    dump(data[: args.limit])


def cmd_price(args):
    params = {"token_id": args.token_id}
    if args.side:
        params["side"] = args.side
    data = get_json("%s/price" % CLOB_BASE, params=params)
    dump(data)


def cmd_raw(args):
    params = {}
    for item in args.param:
        if "=" not in item:
            raise SystemExit("Expected key=value for --param")
        key, value = item.split("=", 1)
        params[key] = value
    base = GAMMA_BASE if args.surface == "gamma" else CLOB_BASE
    data = get_json("%s%s" % (base, args.path), params=params or None)
    dump(data)


def build_parser():
    parser = argparse.ArgumentParser(description="Read Polymarket market and price data.")
    sub = parser.add_subparsers(dest="command")
    sub.required = True

    markets = sub.add_parser("markets", help="List or filter markets from the Gamma API.")
    markets.add_argument("--query", help="Filter locally by question or slug text.")
    markets.add_argument("--slug", help="Filter locally by exact slug.")
    markets.add_argument("--market-id", help="Filter locally by exact market id.")
    markets.add_argument("--limit", type=int, default=10)
    markets.add_argument("--closed", action="store_true")
    markets.add_argument("--archived", action="store_true")
    markets.set_defaults(func=cmd_markets)

    events = sub.add_parser("events", help="List or filter events from the Gamma API.")
    events.add_argument("--query", help="Filter locally by title or slug text.")
    events.add_argument("--limit", type=int, default=10)
    events.set_defaults(func=cmd_events)

    price = sub.add_parser("price", help="Fetch token price from the CLOB API.")
    price.add_argument("--token-id", required=True)
    price.add_argument("--side", choices=["buy", "sell"])
    price.set_defaults(func=cmd_price)

    raw = sub.add_parser("raw", help="Issue a read-only GET to Gamma or CLOB.")
    raw.add_argument("--surface", choices=["gamma", "clob"], required=True)
    raw.add_argument("--path", required=True, help="Path beginning with '/'.")
    raw.add_argument("--param", action="append", default=[], help="Query param as key=value.")
    raw.set_defaults(func=cmd_raw)

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
