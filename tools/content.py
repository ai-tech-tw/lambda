"""Tools for fetching and extracting web page content."""

import re
from collections import deque
from urllib.parse import urlparse

import requests
from scrapy.http import HtmlResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.selector import Selector


def _extract_text(html: str) -> str:
    selector = Selector(text=html)
    text_nodes = selector.xpath(
        "//body//text()[not(ancestor::script) and not(ancestor::style)]"
    ).getall()
    return re.sub(r"\s+", " ", " ".join(text_nodes)).strip()


def _normalize_urls(urls: str) -> list[str]:
    candidates = [x.strip() for x in re.split(r"[\n,]", urls) if x.strip()]
    normalized: list[str] = []
    for raw in candidates:
        normalized_url = (
            raw if raw.startswith(("http://", "https://")) else f"https://{raw}"
        )
        parsed = urlparse(normalized_url)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            normalized.append(normalized_url)
    return normalized


def fetch_content(
    urls: str,
    timeout: int = 20,
    max_chars_per_url: int = 4000,
    max_depth: int = 2,
    regex_pattern: str = "",
    regex_ignore_case: bool = True,
    max_matches_per_url: int = 20,
) -> str:
    """Fetch readable text from URLs; optionally regex-search extracted content."""
    targets = _normalize_urls(urls)
    if not targets:
        return "Error: no valid URLs provided"

    timeout = max(3, min(timeout, 60))
    max_chars_per_url = max(500, min(max_chars_per_url, 10000))
    max_depth = max(0, min(max_depth, 3))
    max_matches_per_url = max(1, min(max_matches_per_url, 100))

    regex_obj = None
    if regex_pattern.strip():
        flags = re.IGNORECASE if regex_ignore_case else 0
        try:
            regex_obj = re.compile(regex_pattern, flags)
        except re.error as exc:
            return f"Error: invalid regex pattern: {exc}"

    blocks: list[str] = []
    headers = {"User-Agent": "lambda/1.0"}
    queue: deque[tuple[str, int]] = deque((target, 0) for target in targets[:5])
    seen: set[str] = set()

    while queue and len(blocks) < 12:
        current_url, depth = queue.popleft()
        if current_url in seen:
            continue
        seen.add(current_url)

        try:
            resp = requests.get(current_url, timeout=timeout, headers=headers)
            resp.raise_for_status()
            content_type = (resp.headers.get("content-type") or "").lower()
            if "text/html" not in content_type:
                text = (resp.text or "").strip()[:max_chars_per_url]
                if regex_obj is None:
                    blocks.append(
                        f"URL: {current_url}\n{text or '(Empty text content)'}"
                    )
                else:
                    matches = [m.group(0) for m in regex_obj.finditer(text or "")][
                        :max_matches_per_url
                    ]
                    match_section = (
                        "\n".join(f"- {m}" for m in matches)
                        if matches
                        else "(No regex match)"
                    )
                    blocks.append(
                        f"URL: {current_url}\nRegex matches ({len(matches)}):\n{match_section}"
                    )
                continue

            html = resp.text
            text = _extract_text(html)[:max_chars_per_url]
            if regex_obj is None:
                blocks.append(f"URL: {current_url}\n{text or '(Empty text content)'}")
            else:
                matches = [m.group(0) for m in regex_obj.finditer(text or "")][
                    :max_matches_per_url
                ]
                match_section = (
                    "\n".join(f"- {m}" for m in matches)
                    if matches
                    else "(No regex match)"
                )
                blocks.append(
                    f"URL: {current_url}\nRegex matches ({len(matches)}):\n{match_section}"
                )

            if depth >= max_depth:
                continue

            response = HtmlResponse(
                url=current_url,
                body=resp.content,
                encoding=resp.encoding or "utf-8",
            )
            current_host = urlparse(current_url).hostname or ""
            extractor = (
                LinkExtractor(allow_domains=[current_host])
                if current_host
                else LinkExtractor()
            )
            for link in extractor.extract_links(response):
                if link.url not in seen:
                    queue.append((link.url, depth + 1))
        except Exception as exc:
            blocks.append(f"URL: {current_url}\nError: {exc}")

    return "\n\n".join(blocks)
