"""
Scraper da wiki oficial do Rubinot (wiki.rubinot.com).
A wiki não usa Cloudflare agressivo — acessível com requests normal.
Fornece dados de hunts, quests, itens e bosses sempre atualizados.
"""

import re
import logging
import requests
from bs4 import BeautifulSoup
from cache import TTLCache

logger = logging.getLogger(__name__)

WIKI_BASE = "https://wiki.rubinot.com"

_cache = TTLCache()
_session = requests.Session()
_session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
})


def _get(url: str, timeout: int = 10) -> requests.Response | None:
    """GET simples com fallback SSL."""
    try:
        resp = _session.get(url, timeout=timeout)
        if resp.status_code == 200:
            return resp
        logger.warning("wiki GET %s → %s", url, resp.status_code)
    except requests.exceptions.SSLError:
        try:
            resp = _session.get(url, timeout=timeout, verify=False)
            if resp.status_code == 200:
                return resp
        except Exception:
            pass
    except Exception as e:
        logger.warning("wiki GET %s falhou: %s", url, e)
    return None


def _clean_text(text: str) -> str:
    """Remove espaços extras e linhas em branco duplicadas."""
    lines = [l.strip() for l in text.splitlines()]
    lines = [l for l in lines if l]
    return "\n".join(lines)


# ── Busca genérica na wiki ────────────────────────────────────────────────────

def search_wiki(query: str) -> list[dict]:
    """
    Busca páginas na wiki por termo.
    Retorna lista de {title, url, snippet}.
    Cache de 1 hora.
    """
    cache_key = f"wiki:search:{query.lower()}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    # MediaWiki search endpoint (funciona na maioria dos wikis)
    url = f"{WIKI_BASE}/index.php?search={requests.utils.quote(query)}&title=Special:Search"
    resp = _get(url)
    if not resp:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    # Resultados padrão do MediaWiki
    for li in soup.select(".mw-search-results li, .searchresults li")[:5]:
        title_tag = li.find("a")
        snippet_tag = li.find(class_=re.compile(r"search.*result.*text|searchresult"))
        if title_tag:
            results.append({
                "title": title_tag.get_text(strip=True),
                "url": WIKI_BASE + title_tag.get("href", ""),
                "snippet": snippet_tag.get_text(strip=True)[:200] if snippet_tag else "",
            })

    # Fallback: redirecionou direto para uma página
    if not results and soup.find("h1", id="firstHeading"):
        heading = soup.find("h1", id="firstHeading").get_text(strip=True)
        results.append({
            "title": heading,
            "url": resp.url,
            "snippet": _extract_first_paragraph(soup),
        })

    _cache.set(cache_key, results, ttl_seconds=3600)
    return results


def _extract_first_paragraph(soup: BeautifulSoup) -> str:
    """Extrai primeiro parágrafo útil do conteúdo da wiki."""
    content = soup.find(id="mw-content-text") or soup.find(class_="mw-parser-output")
    if content:
        for p in content.find_all("p"):
            text = p.get_text(strip=True)
            if len(text) > 50:
                return text[:300]
    return ""


# ── Página específica da wiki ─────────────────────────────────────────────────

def get_wiki_page(page_name: str) -> dict | None:
    """
    Busca uma página específica da wiki pelo nome.
    Ex: get_wiki_page("Soulpit"), get_wiki_page("Linked_Tasks")
    Cache de 2 horas.
    """
    cache_key = f"wiki:page:{page_name.lower()}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    # Tenta URL direta e variações
    urls_to_try = [
        f"{WIKI_BASE}/wiki/{requests.utils.quote(page_name.replace(' ', '_'))}",
        f"{WIKI_BASE}/{requests.utils.quote(page_name.replace(' ', '_'))}",
        f"{WIKI_BASE}/index.php/{requests.utils.quote(page_name.replace(' ', '_'))}",
    ]

    resp = None
    used_url = ""
    for url in urls_to_try:
        resp = _get(url)
        if resp:
            used_url = url
            break

    if not resp:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Verifica se a página existe
    heading = soup.find("h1", id="firstHeading")
    if not heading:
        return None

    title = heading.get_text(strip=True)

    # Extrai conteúdo principal
    content_div = soup.find(id="mw-content-text") or soup.find(class_="mw-parser-output")
    if not content_div:
        return None

    # Remove elementos desnecessários (navigation, templates de aviso, etc.)
    for tag in content_div.find_all(["table", "div"], class_=re.compile(r"navbox|toc|mw-empty")):
        tag.decompose()

    # Extrai seções principais
    sections = {}
    current_section = "intro"
    current_text = []

    for elem in content_div.find_all(["h2", "h3", "p", "ul", "ol", "table"]):
        if elem.name in ("h2", "h3"):
            if current_text:
                sections[current_section] = "\n".join(current_text)
            current_section = elem.get_text(strip=True).replace("[edit]", "").strip()
            current_text = []
        elif elem.name == "p":
            text = elem.get_text(strip=True)
            if text:
                current_text.append(text)
        elif elem.name in ("ul", "ol"):
            for li in elem.find_all("li"):
                text = li.get_text(strip=True)
                if text:
                    current_text.append(f"• {text}")
        elif elem.name == "table":
            # Extrai tabelas como texto formatado
            table_text = _table_to_text(elem)
            if table_text:
                current_text.append(table_text)

    if current_text:
        sections[current_section] = "\n".join(current_text)

    # Texto completo (limitado para não explodir o prompt)
    full_text = _clean_text(content_div.get_text())[:3000]

    result = {
        "title": title,
        "url": used_url,
        "sections": sections,
        "full_text": full_text,
        "intro": sections.get("intro", _extract_first_paragraph(soup)),
    }

    _cache.set(cache_key, result, ttl_seconds=7200)
    return result


def _table_to_text(table) -> str:
    """Converte tabela HTML em texto simples."""
    rows = []
    for tr in table.find_all("tr")[:15]:
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if any(cells):
            rows.append(" | ".join(cells))
    return "\n".join(rows) if rows else ""


# ── Linked Tasks ──────────────────────────────────────────────────────────────

def get_linked_tasks() -> dict | None:
    """Busca dados das Linked Tasks na wiki."""
    cache_key = "wiki:linked_tasks"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    page = get_wiki_page("Linked_Tasks")
    if not page:
        page = get_wiki_page("Linked Tasks")
    if not page:
        # Tenta URL conhecida
        resp = _get(f"{WIKI_BASE}/wiki/Linked_Tasks")
        if resp:
            soup = BeautifulSoup(resp.text, "html.parser")
            full_text = _clean_text(soup.get_text())[:3000]
            page = {"title": "Linked Tasks", "url": resp.url, "full_text": full_text}

    if page:
        _cache.set(cache_key, page, ttl_seconds=7200)
    return page


# ── Soulpit ───────────────────────────────────────────────────────────────────

def get_soulpit_info() -> dict | None:
    """Busca dados do Soulpit na wiki."""
    cache_key = "wiki:soulpit"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    for name in ["Soulpit", "Soul_Pit", "Soul Pit"]:
        page = get_wiki_page(name)
        if page:
            _cache.set(cache_key, page, ttl_seconds=7200)
            return page
    return None


# ── Quests ────────────────────────────────────────────────────────────────────

def get_quest_info(quest_name: str) -> dict | None:
    """Busca guia de uma quest específica na wiki."""
    cache_key = f"wiki:quest:{quest_name.lower()}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    # Tenta variações do nome
    variations = [
        quest_name,
        quest_name.replace(" ", "_"),
        f"{quest_name}_Quest",
        f"{quest_name.replace(' ', '_')}_Quest",
    ]
    for name in variations:
        page = get_wiki_page(name)
        if page:
            _cache.set(cache_key, page, ttl_seconds=7200)
            return page
    return None


# ── Bosses ────────────────────────────────────────────────────────────────────

def get_boss_info(boss_name: str) -> dict | None:
    """Busca dados de um boss específico na wiki."""
    cache_key = f"wiki:boss:{boss_name.lower()}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    page = get_wiki_page(boss_name)
    if page:
        _cache.set(cache_key, page, ttl_seconds=7200)
    return page


# ── Spots de Hunt ─────────────────────────────────────────────────────────────

def get_hunt_spot(spot_name: str) -> dict | None:
    """Busca dados de um spot de hunt na wiki."""
    cache_key = f"wiki:hunt:{spot_name.lower()}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    page = get_wiki_page(spot_name)
    if page:
        _cache.set(cache_key, page, ttl_seconds=7200)
    return page


# ── Formatação para Discord ───────────────────────────────────────────────────

def format_wiki_result(page: dict, max_chars: int = 3500) -> str:
    """Formata resultado da wiki para embed Discord."""
    if not page:
        return "Página não encontrada na wiki."

    lines = []
    if page.get("intro"):
        lines.append(page["intro"][:500])
        lines.append("")

    if page.get("sections"):
        for section_name, section_text in list(page["sections"].items())[:4]:
            if section_name == "intro":
                continue
            lines.append(f"**{section_name}**")
            lines.append(section_text[:400])
            lines.append("")

    result = "\n".join(lines)
    if len(result) < 100 and page.get("full_text"):
        result = page["full_text"]

    return result[:max_chars] if result else "Sem conteúdo disponível."


def format_search_results(results: list[dict]) -> str:
    """Formata resultados de busca para embed Discord."""
    if not results:
        return "Nenhum resultado encontrado na wiki."
    lines = []
    for r in results:
        title = r.get("title", "?")
        url = r.get("url", "")
        snippet = r.get("snippet", "")
        lines.append(f"📄 **[{title}]({url})**")
        if snippet:
            lines.append(f"_{snippet[:150]}_")
        lines.append("")
    return "\n".join(lines)[:3500]
