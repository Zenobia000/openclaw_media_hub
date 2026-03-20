#!/usr/bin/env python3
"""Search the web for topic information using DuckDuckGo HTML search.

Uses subprocess to call curl — no API key needed.
Outputs a JSON array of {title, url, snippet} to stdout.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.parse
from typing import TypedDict


class SearchResult(TypedDict):
    title: str
    url: str
    snippet: str


def build_search_url(topic: str, language: str = "zh-TW") -> str:
    """Build a DuckDuckGo HTML search URL."""
    params = urllib.parse.urlencode({
        "q": topic,
        "kl": _lang_to_region(language),
        "df": "d",  # past day
    })
    return f"https://html.duckduckgo.com/html/?{params}"


def _lang_to_region(language: str) -> str:
    """Map language code to DuckDuckGo region code."""
    mapping: dict[str, str] = {
        "zh-TW": "tw-tzh",
        "zh-CN": "cn-zh",
        "en": "us-en",
        "ja": "jp-ja",
    }
    return mapping.get(language, "wt-wt")


def fetch_html(url: str) -> str:
    """Fetch HTML content via curl subprocess."""
    result = subprocess.run(
        [
            "curl",
            "-s",
            "-L",
            "-A", "Mozilla/5.0 (compatible; OpenClaw/1.0)",
            "--max-time", "15",
            url,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(
            json.dumps({"error": f"curl failed with code {result.returncode}: {result.stderr.strip()}"}),
            file=sys.stderr,
        )
        sys.exit(1)
    return result.stdout


def parse_results(html: str, max_results: int) -> list[SearchResult]:
    """Parse DuckDuckGo HTML search results.

    DuckDuckGo HTML results use <a class="result__a"> for titles/links
    and <a class="result__snippet"> for snippets.
    """
    results: list[SearchResult] = []

    # Match result blocks — each result lives inside a div.result
    # Extract title+url from <a class="result__a" ...>
    title_pattern = re.compile(
        r'<a[^>]+class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
        re.DOTALL,
    )
    snippet_pattern = re.compile(
        r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
        re.DOTALL,
    )

    titles = title_pattern.findall(html)
    snippets = snippet_pattern.findall(html)

    for i, (raw_url, raw_title) in enumerate(titles):
        if i >= max_results:
            break

        # Clean HTML tags from title and snippet
        title = _strip_html(raw_title).strip()
        url = _extract_url(raw_url)
        snippet = _strip_html(snippets[i]).strip() if i < len(snippets) else ""

        if not title or not url:
            continue

        results.append(SearchResult(title=title, url=url, snippet=snippet))

    return results


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#x27;", "'")
    text = text.replace("&nbsp;", " ")
    return text.strip()


def _extract_url(raw_url: str) -> str:
    """Extract the actual URL from DuckDuckGo redirect links."""
    # DuckDuckGo wraps URLs in a redirect: //duckduckgo.com/l/?uddg=<encoded_url>&...
    if "uddg=" in raw_url:
        match = re.search(r"uddg=([^&]+)", raw_url)
        if match:
            return urllib.parse.unquote(match.group(1))
    # Direct URL
    if raw_url.startswith("http"):
        return raw_url
    if raw_url.startswith("//"):
        return "https:" + raw_url
    return raw_url


def search(topic: str, max_results: int = 5, language: str = "zh-TW") -> list[SearchResult]:
    """Run a web search and return parsed results."""
    url = build_search_url(topic, language)
    html = fetch_html(url)
    return parse_results(html, max_results)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search the web for topic information using DuckDuckGo HTML search.",
    )
    parser.add_argument(
        "--topic",
        required=True,
        help="Search topic / keywords (e.g. 'AI 產業動態')",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="Maximum number of results to return (default: 5)",
    )
    parser.add_argument(
        "--language",
        default="zh-TW",
        help="Search language / region (default: zh-TW)",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    try:
        results = search(
            topic=args.topic,
            max_results=args.max_results,
            language=args.language,
        )
        print(json.dumps(results, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)
