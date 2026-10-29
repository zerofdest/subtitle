"""Remove IP information and automatic_captions from *.info.json files in this script's folder.
Files are overwritten without backup. Requires Python 3.9+."""

import ipaddress
import json
import os
import re
import tempfile
from pathlib import Path

FOLDER = Path(r"H:\yt-dlp\output\NA")
IP_FIELDS = {
    "ip", "ip_address", "ipaddr", "ipv4", "ipv6", "ipv4_address",
    "ipv6_address", "client_ip", "remote_ip", "public_ip", "local_ip",
    "source_ip", "server_ip", "origin_ip", "proxy_ip", "external_ip",
    "x-forwarded-for", "x-real-ip", "true-client-ip", "cf-connecting-ip",
}
IP_PARAM = re.compile(
    r"([?&])(?:ip|ip_address|ipv4|ipv6|client_ip|remote_ip|public_ip)=[^&#]*",
    re.IGNORECASE,
)
IPV4 = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
IPV6 = re.compile(
    r"(?<![\w])(?:[0-9a-fA-F]{0,4}:){2,}(?:[0-9a-fA-F]{0,4})?(?![\w])"
)


def scrub_string(value):
    value = IP_PARAM.sub(lambda m: "?" if m.group(1) == "?" else "", value)
    value = value.replace("?&", "?")
    value = re.sub(r"\?(?=#|$)", "", value)

    def replace_address(match):
        candidate = match.group()
        try:
            ipaddress.ip_address(candidate)
        except ValueError:
            return candidate
        return "[IP_REMOVED]"

    return IPV6.sub(replace_address, IPV4.sub(replace_address, value))


def scrub(value):
    if isinstance(value, dict):
        return {
            key: scrub(item)
            for key, item in value.items()
            if key.lower() not in IP_FIELDS
        }
    if isinstance(value, list):
        return [scrub(item) for item in value]
    if isinstance(value, str):
        return scrub_string(value)
    return value


def process(path):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    cleaned = scrub(data)
    cleaned.pop("automatic_captions", None)
    if cleaned == data:
        print(f"SKIP: {path.name}")
        return

    # A temporary output file prevents partial JSON writes; no backup is kept.
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".tmp", prefix="ipclean_",
            dir=path.parent, delete=False
        ) as output:
            tmp = Path(output.name)
            json.dump(cleaned, output, ensure_ascii=False, indent=2)
            output.write("\n")
        os.replace(tmp, path)
    finally:
        if tmp and tmp.exists():
            tmp.unlink()
    print(f"CLEANED: {path.name}")


def main():
    paths = sorted(FOLDER.glob("*.info.json"))
    if not paths:
        print("No *.info.json files found.")
        return
    for path in paths:
        try:
            process(path)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            print(f"ERROR: {path.name}: {exc}")


if __name__ == "__main__":
    main()
