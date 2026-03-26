#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VPN_HELPER = os.path.join(SCRIPT_DIR, "vpn_helper.py")
TRADE = os.path.join(SCRIPT_DIR, "trade.py")


def dump(data):
    print(json.dumps(data, indent=2, sort_keys=True, default=str))


def fail(message, **details):
    payload = {"error": message}
    if details:
        payload["details"] = details
    print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
    raise SystemExit(1)


def base_env():
    env = os.environ.copy()
    proxy = env.get("MIHOMO_PROXY", "http://127.0.0.1:7890")
    env["HTTP_PROXY"] = proxy
    env["HTTPS_PROXY"] = proxy
    env["ALL_PROXY"] = proxy
    return env


def run_json(cmd, env=None, check=True):
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if check and result.returncode != 0:
        try:
            payload = json.loads(result.stderr.strip() or result.stdout.strip())
        except Exception:
            payload = {
                "command": cmd,
                "returncode": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
            }
        fail("Command failed.", command=cmd, result=payload)
    text = result.stdout.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "raw_stdout": text,
            "raw_stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }


def uv_prefix(with_package):
    return ["uv", "run", "--python", "3.11", "--with", with_package]


def check_geoblock():
    cmd = uv_prefix("requests") + [VPN_HELPER, "geoblock"]
    return run_json(cmd, check=False)


def select_proxy(group, proxy):
    cmd = uv_prefix("requests") + [VPN_HELPER, "select", "--group", group, "--proxy", proxy]
    return run_json(cmd)


def ensure_allowed_region(group, proxies, force_switch=False):
    initial = check_geoblock()
    if "geoblock" in initial and not force_switch:
        return {"status": "already_allowed", "geoblock": initial["geoblock"]}

    attempts = []
    for proxy in proxies:
        attempts.append({"proxy": proxy, "select": select_proxy(group, proxy)})
        result = check_geoblock()
        attempts[-1]["geoblock"] = result
        if "geoblock" in result:
            return {
                "status": "switched",
                "selected_proxy": proxy,
                "geoblock": result["geoblock"],
                "attempts": attempts,
            }

    fail(
        "Unable to find an allowed Polymarket exit through the configured Mihomo selector.",
        group=group,
        attempted_proxies=proxies,
        attempts=attempts,
    )


def run_trade_command(trade_args):
    cmd = uv_prefix("py-clob-client") + [TRADE] + trade_args
    return run_json(cmd, env=base_env())


def build_parser():
    parser = argparse.ArgumentParser(
        description="Run Polymarket trade.py through a local Mihomo proxy after verifying geoblock."
    )
    parser.add_argument(
        "--group",
        default="良心云",
        help="Mihomo selector group used to switch exits before trading.",
    )
    parser.add_argument(
        "--proxy",
        action="append",
        default=[],
        help="Candidate proxy name to try when the current exit is blocked. Repeatable.",
    )
    parser.add_argument(
        "--skip-switch",
        action="store_true",
        help="Do not switch proxies automatically. Only verify geoblock and then run trade.py.",
    )
    parser.add_argument(
        "--force-switch",
        action="store_true",
        help="Always try the provided candidate proxies even if the current exit is already allowed.",
    )
    parser.add_argument(
        "trade_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed through to trade.py. Prefix with -- before the trade.py subcommand.",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    trade_args = args.trade_args
    if trade_args and trade_args[0] == "--":
        trade_args = trade_args[1:]
    if not trade_args:
        fail(
            "Missing trade.py arguments.",
            hint="Example: trade_with_vpn.py --proxy '🇭🇰香港高速01|BGP|流媒体' -- market-order --token-id ... --submit",
        )

    if args.skip_switch:
        geoblock = run_json(uv_prefix("requests") + [VPN_HELPER, "geoblock"])
        vpn = {"status": "checked_only", "geoblock": geoblock.get("geoblock")}
    elif args.force_switch:
        if not args.proxy:
            fail(
                "No candidate proxies were provided for --force-switch.",
                hint="Pass one or more --proxy values.",
            )
        vpn = ensure_allowed_region(args.group, args.proxy, force_switch=True)
    else:
        vpn = ensure_allowed_region(args.group, args.proxy)

    trade = run_trade_command(trade_args)
    dump({"vpn": vpn, "trade": trade})


if __name__ == "__main__":
    main()
