from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
)


def load_wrangler_account_id() -> str:
    command = [r"C:\Users\walid\AppData\Roaming\npm\wrangler.cmd", "whoami"]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    except Exception:
        return ""
    if completed.returncode != 0:
        return ""
    for line in completed.stdout.splitlines():
        if "Account ID" not in line:
            continue
        parts = [part.strip() for part in line.replace("â”‚", "│").split("│") if part.strip()]
        if parts:
            candidate = parts[-1]
            if len(candidate) == 32:
                return candidate
    return ""


def resolve_cloudflare_credentials() -> tuple[str, str]:
    token = (
        os.environ.get("CLOUDFLARE_API_TOKEN")
        or os.environ.get("CF_API_TOKEN")
        or os.environ.get("CLOUDFLARE_BROWSER_RENDERING_TOKEN")
        or ""
    ).strip()
    account_id = (
        os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        or os.environ.get("CF_ACCOUNT_ID")
        or load_wrangler_account_id()
    ).strip()
    return token, account_id


def fetch_cloudflare_endpoint(url: str, endpoint_name: str, *, token: str, account_id: str) -> Any:
    endpoint = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/browser-rendering/{endpoint_name}"
    payload = json.dumps({"url": url}).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        data = json.loads(response.read().decode("utf-8", "replace"))
    return data.get("result")


def fetch_cloudflare_content(url: str, *, token: str, account_id: str) -> str:
    result = fetch_cloudflare_endpoint(url, "content", token=token, account_id=account_id)
    if isinstance(result, str):
        return result
    result = result or {}
    return result.get("content") or result.get("html") or ""


def fetch_cloudflare_markdown(url: str, *, token: str, account_id: str) -> tuple[str, str]:
    result = fetch_cloudflare_endpoint(url, "markdown", token=token, account_id=account_id)
    if isinstance(result, str):
        return result, url
    result = result or {}
    return result.get("markdown") or result.get("content") or "", result.get("url") or url


def fetch_direct_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.7"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", "replace")


def fetch_direct_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.7"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html or "", "html.parser")
    return " ".join(soup.get_text(" ", strip=True).split())
