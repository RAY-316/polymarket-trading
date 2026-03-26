#!/usr/bin/env python3
import argparse
import json
import os
import sys

import requests
from requests import exceptions as req_exc


def dump(data):
    print(json.dumps(data, indent=2, sort_keys=True))


def controller_base():
    return os.getenv("MIHOMO_CONTROLLER", "http://127.0.0.1:9090").rstrip("/")


def proxy_url():
    return os.getenv("MIHOMO_PROXY", "http://127.0.0.1:7890")


def fail(message, **details):
    payload = {"error": message}
    if details:
        payload["details"] = details
    print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
    raise SystemExit(1)


def proxied_session():
    proxy = proxy_url()
    session = requests.Session()
    session.proxies.update(
        {
            "http": proxy,
            "https": proxy,
        }
    )
    return session


def request_json(method, path, payload=None):
    url = "%s%s" % (controller_base(), path)
    try:
        response = requests.request(method, url, json=payload, timeout=20)
    except req_exc.ConnectionError as exc:
        fail(
            "Cannot reach the Mihomo controller.",
            controller=controller_base(),
            hint="Check that Mihomo is running and that MIHOMO_CONTROLLER points to the REST API.",
            cause=str(exc),
        )
    except req_exc.Timeout as exc:
        fail(
            "Timed out while talking to the Mihomo controller.",
            controller=controller_base(),
            hint="Check that the Mihomo REST API is responsive.",
            cause=str(exc),
        )
    response.raise_for_status()
    if not response.text:
        return {}
    return response.json()


def quoted_group_path(group):
    return "/proxies/%s" % requests.utils.quote(group, safe="")


def require_group(group):
    data = request_json("GET", quoted_group_path(group))
    if data.get("type") != "Selector":
        fail(
            "The requested Mihomo group is not a selector.",
            group=group,
            actual_type=data.get("type"),
        )
    return data


def request_through_proxy(url):
    session = proxied_session()
    try:
        return session.get(url, timeout=20)
    except req_exc.ProxyError as exc:
        fail(
            "The local proxy is unreachable.",
            proxy=proxy_url(),
            hint="Check that Mihomo is listening on the mixed proxy port and that MIHOMO_PROXY is correct.",
            cause=str(exc),
        )
    except req_exc.ConnectionError as exc:
        fail(
            "Failed to reach the remote site through the local proxy.",
            proxy=proxy_url(),
            url=url,
            hint="The selected node may be down, blocked, or not actually routed through Mihomo.",
            cause=str(exc),
        )
    except req_exc.Timeout as exc:
        fail(
            "Timed out while using the local proxy.",
            proxy=proxy_url(),
            url=url,
            hint="Try another node or recheck the proxy port.",
            cause=str(exc),
        )


def cmd_groups(_args):
    data = request_json("GET", "/proxies")
    groups = []
    for name, item in data.get("proxies", {}).items():
        if item.get("type") == "Selector":
            groups.append(
                {
                    "name": name,
                    "now": item.get("now"),
                    "options": item.get("all", []),
                }
            )
    dump(groups)


def cmd_current(args):
    data = require_group(args.group)
    dump(
        {
            "group": data.get("name"),
            "current": data.get("now"),
            "options": data.get("all", []),
            "alive": data.get("alive"),
        }
    )


def cmd_select(args):
    current = require_group(args.group)
    options = current.get("all", [])
    if args.proxy not in options:
        fail(
            "The requested proxy is not in the selector group.",
            group=args.group,
            requested_proxy=args.proxy,
            available=options,
        )
    request_json("PUT", quoted_group_path(args.group), {"name": args.proxy})
    data = require_group(args.group)
    dump(
        {
            "group": data.get("name"),
            "current": data.get("now"),
            "proxy_url": proxy_url(),
        }
    )


def cmd_ip(_args):
    ip = request_through_proxy("https://api.ipify.org").text.strip()
    try:
        info = request_through_proxy("https://ipinfo.io/json").json()
    except Exception:
        info = {"warning": "Failed to decode ipinfo response."}
    dump({"ip": ip, "ipinfo": info, "proxy_url": proxy_url()})


def cmd_geoblock(_args):
    result = request_through_proxy("https://polymarket.com/api/geoblock").json()
    if result.get("blocked") is True:
        fail(
            "Polymarket still reports the proxied exit as blocked.",
            proxy=proxy_url(),
            ip=result.get("ip"),
            country=result.get("country"),
            region=result.get("region"),
            hint="Switch the Mihomo selector to another allowed region and retry.",
        )
    dump({"proxy_url": proxy_url(), "geoblock": result})


def build_parser():
    parser = argparse.ArgumentParser(description="Control a local Mihomo proxy for Polymarket trading.")
    sub = parser.add_subparsers(dest="command")
    sub.required = True

    groups = sub.add_parser("groups", help="List Mihomo selector groups and current choices.")
    groups.set_defaults(func=cmd_groups)

    current = sub.add_parser("current", help="Show the active proxy in one selector group.")
    current.add_argument("--group", default="良心云")
    current.set_defaults(func=cmd_current)

    select = sub.add_parser("select", help="Switch a Mihomo selector group to a specific node.")
    select.add_argument("--group", default="良心云")
    select.add_argument("--proxy", required=True)
    select.set_defaults(func=cmd_select)

    ip = sub.add_parser("ip", help="Show the proxied public IP and ipinfo details.")
    ip.set_defaults(func=cmd_ip)

    geoblock = sub.add_parser("geoblock", help="Check Polymarket geoblock through the local proxy.")
    geoblock.set_defaults(func=cmd_geoblock)

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
