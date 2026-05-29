"""
Scraper de fóruns: OtLand e busca via DuckDuckGo (sem API key necessária).
Busca threads, guias e discussões sobre Rubinot na comunidade.
"""

import re
import logging
import requests
from bs4 import BeautifulSoup
from cache import TTLCache
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

_cache = TTLCache()   # TTL 2h para resultados de fórum

DDGO_URL   = "https://html.duckduckgo.com/html/"
OTLAND_URL = "https://otland.net"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
}

_session = requests.Session()
_session.headers.update(HEADERS)


# ── DuckDuckGo (sem API key) ──────────────────────────────────────────────────

def search_ddgo(query: str, site: str = "", max_results: int = 5) -> list[dict]:
    """
    Busca no DuckDuckGo sem API key (scraping da versão HTML).
    Retorna lista de {title, url, snippet}.
    """
    full_query = f"site:{site} {query}" if site else query
    cache_key = f"ddgo:{full_query.lower()}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        resp = _session.post(
            DDGO_URL,
            data={"q": full_query, "kl": "br-pt"},
            timeout=8,
        )
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        results = []

        for result in soup.select(".result")[:max_results]:
            title_el = result.select_one(".result__title")
            url_el   = result.select_one(".result__url")
            snip_el  = result.select_one(".result__snippet")

            title   = title_el.get_text(strip=True) if title_el else ""
            url_raw = url_el.get_text(strip=True) if url_el else ""
            snippet = snip_el.get_text(strip=True) if snip_el else ""

            # Tenta pegar URL real do href
            link_el = result.select_one("a.result__a")
            if link_el and link_el.get("href"):
                href = link_el["href"]
                # DuckDuckGo usa redirects — pegar o uddg param ou o href direto
                if href.startswith("http"):
                    url_raw = href
                elif "uddg=" in href:
                    from urllib.parse import unquote, parse_qs, urlparse
                    params = parse_qs(urlparse(href).query)
                    url_raw = unquote(params.get("uddg", [""])[0]) or url_raw

            if title:
                results.append({"title": title, "url": url_raw, "snippet": snippet})

        _cache.set(cache_key, results, ttl_seconds=7200)
        return results

    except Exception as e:
        logger.warning("DuckDuckGo search erro: %s", e)
        return []


# ── OtLand direto ─────────────────────────────────────────────────────────────

def search_otland(query: str, max_results: int = 5) -> list[dict]:
    """
    Busca diretamente no fórum OtLand.
    Endpoint: otland.net/search/?q=QUERY&t=post
    """
    cache_key = f"otland:{query.lower()}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        url = f"{OTLAND_URL}/search/?q={quote_plus(query)}&t=post&c[child_nodes]=1"
        resp = _session.get(url, timeout=8)
        if resp.status_code != 200:
            # Fallback para DuckDuckGo buscando no OtLand
            return search_ddgo(f"rubinot {query}", site="otland.net", max_results=max_results)

        soup = BeautifulSoup(resp.text, "html.parser")
        results = []

        for item in soup.select(".contentRow")[:max_results]:
            title_el   = item.select_one(".contentRow-title a")
            snippet_el = item.select_one(".contentRow-snippet")
            date_el    = item.select_one("time")

            if not title_el:
                continue

            title   = title_el.get_text(strip=True)
            url_raw = OTLAND_URL + title_el.get("href", "")
            snippet = snippet_el.get_text(strip=True)[:200] if snippet_el else ""
            date    = date_el.get("title", "") if date_el else ""

            results.append({
                "title": title,
                "url": url_raw,
                "snippet": snippet,
                "date": date,
            })

        if not results:
            # Fallback DuckDuckGo
            results = search_ddgo(f"rubinot {query}", site="otland.net", max_results=max_results)

        _cache.set(cache_key, results, ttl_seconds=7200)
        return results

    except Exception as e:
        logger.warning("OtLand search erro: %s — usando DuckDuckGo", e)
        return search_ddgo(f"rubinot {query}", site="otland.net", max_results=max_results)


# ── Função principal pública ──────────────────────────────────────────────────

def search_forum(query: str, max_results: int = 5) -> list[dict]:
    """
    Busca em fóruns (OtLand primeiro, DuckDuckGo como fallback).
    Adiciona "rubinot" ao query automaticamente para contexto.
    """
    rubinot_query = query if "rubinot" in query.lower() else f"rubinot {query}"
    results = search_otland(rubinot_query, max_results=max_results)
    if not results:
        # Tenta busca mais ampla
        results = search_ddgo(rubinot_query, max_results=max_results)
    return results


def format_forum_results(results: list[dict], title: str = "Resultados do Fórum") -> str:
    """Formata resultados para Discord embed."""
    if not results:
        return "Nenhum resultado encontrado no fórum."
    lines = [f"**{title}**\n"]
    for r in results:
        url   = r.get("url", "")
        t     = r.get("title", "Sem título")[:80]
        snip  = r.get("snippet", "")[:120]
        date  = f" *({r['date'][:10]})*" if r.get("date") else ""
        if url:
            lines.append(f"📄 [{t}]({url}){date}")
        else:
            lines.append(f"📄 **{t}**{date}")
        if snip:
            lines.append(f"   *{snip}...*")
        lines.append("")
    return "\n".join(lines)[:3500]
