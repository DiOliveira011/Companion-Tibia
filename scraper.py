"""
Scraper do servidor Rubinot.
Busca personagens, guilds, highscores, noticias e status via HTTP.
Usa cloudscraper para bypassar a protecao Cloudflare do site.
"""

import re
import time
import logging
import requests
from bs4 import BeautifulSoup
from cache import character_cache

logger = logging.getLogger(__name__)

RUBINOT_BASE = "https://rubinot.com.br"

# ── Cliente HTTP ─────────────────────────────────────────────────────────────
# cloudscraper resolve o desafio JS do Cloudflare automaticamente.
# Fallback para requests.Session se nao estiver instalado.

try:
    import cloudscraper
    _session = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )
    logger.info("cloudscraper ativo — Cloudflare bypass habilitado")
except ImportError:
    logger.warning("cloudscraper nao encontrado — usando requests (pode falhar no Cloudflare)")
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


def _get(url: str, timeout: int = 12) -> requests.Response | None:
    """GET com retry e fallback SSL para proxies corporativos."""
    for attempt in range(3):
        try:
            time.sleep(0.4 * attempt)
            resp = _session.get(url, timeout=timeout)
            print(f"GET {url} → {resp.status_code}")
            if resp.status_code == 200:
                return resp
            logger.warning("GET %s → %s", url, resp.status_code)
        except requests.exceptions.SSLError:
            try:
                resp = _session.get(url, timeout=timeout, verify=False)
                if resp.status_code == 200:
                    return resp
            except Exception:
                pass
        except Exception as e:
            logger.warning("GET %s falhou (tentativa %d): %s", url, attempt + 1, e)
    return None


def _extract_number(text: str) -> int | None:
    """Extrai primeiro numero inteiro de uma string."""
    match = re.search(r"\d+", str(text).replace(",", "").replace(".", ""))
    return int(match.group()) if match else None


def _parse_table_kv(soup: BeautifulSoup) -> dict:
    """Extrai pares label->valor de todas as tabelas da pagina."""
    data = {}
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True).lower().rstrip(":")
                value = cells[1].get_text(strip=True)
                if label and value:
                    data[label] = value
    return data


# ── Personagem ────────────────────────────────────────────────────────────────

def get_character(name: str) -> dict | None:
    """
    Busca dados de um personagem em rubinot.com.br/characters?name=
    Retorna dict com level, vocation, guild, last_login, etc.
    Cache de 10 minutos.
    """
    cache_key = f"char:{name.lower()}"
    cached = character_cache.get(cache_key)
    if cached:
        return cached

    url = f"{RUBINOT_BASE}/characters?name={requests.utils.quote(name)}"
    resp = _get(url)
    if not resp:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    page_text = soup.get_text().lower()

    if any(phrase in page_text for phrase in [
        "not found", "does not exist", "nao encontrado",
        "character not found", "no character",
    ]):
        return None

    data = {"name": name, "found": False, "url": url}
    kv = _parse_table_kv(soup)

    # Mapeamento de labels para campos — cobre portugues e ingles
    for label, value in kv.items():
        if "name" in label and not data.get("name_clean"):
            data["name_clean"] = value.split("(")[0].strip()
        elif "level" in label or "nivel" in label:
            data["level"] = _extract_number(value) or value
        elif "vocation" in label or "vocacao" in label or "vocação" in label:
            data["vocation"] = value
        elif "world" in label or "servidor" in label:
            data["world"] = value
        elif "residence" in label or "city" in label or "cidade" in label:
            data["city"] = value
        elif "guild" in label or "guilda" in label:
            data["guild"] = value
        elif "last login" in label or "last seen" in label or "ultimo" in label:
            data["last_login"] = value
        elif "achievement" in label or "ponto" in label:
            data["achievement_points"] = _extract_number(value)
        elif "comment" in label or "profile" in label:
            data["comment"] = value[:200]
        elif "account status" in label or "status" in label:
            data["account_status"] = value
        elif "balance" in label or "saldo" in label:
            data["balance"] = value
        elif "charm" in label:
            data["charm_points"] = value
        elif "task" in label or "tarefa" in label:
            data["task_points"] = value
        elif "online" in label:
            data["online"] = value

    if data.get("level") or data.get("vocation"):
        data["found"] = True
        character_cache.set(cache_key, data, ttl_seconds=600)
        return data

    # Fallback regex se a tabela nao for padrao
    level_match = re.search(r"[Ll]evel[:\s]+(\d+)", resp.text)
    voc_match   = re.search(r"[Vv]ocation[:\s]+([A-Za-z ]+)", resp.text)
    if level_match or voc_match:
        data["found"] = True
        if level_match:
            data["level"] = int(level_match.group(1))
        if voc_match:
            data["vocation"] = voc_match.group(1).strip()
        character_cache.set(cache_key, data, ttl_seconds=600)
        return data

    return None


def get_party_data(names: list[str]) -> list[dict]:
    """Busca dados de multiplos personagens para analise de party."""
    results = []
    for name in names[:6]:
        char = get_character(name.strip())
        results.append(char if char else {"name": name, "found": False})
        time.sleep(0.8)
    return results


# ── Guild ─────────────────────────────────────────────────────────────────────

def get_guild(name: str) -> dict | None:
    """Busca dados de uma guild em /guilds?name= ou /guilds/{name}."""
    cache_key = f"guild:{name.lower()}"
    cached = character_cache.get(cache_key)
    if cached:
        return cached

    # Tenta URL moderna primeiro, depois formato antigo
    urls_to_try = [
        f"{RUBINOT_BASE}/guilds?name={requests.utils.quote(name)}",
        f"{RUBINOT_BASE}/guilds/{requests.utils.quote(name)}",
        f"{RUBINOT_BASE}/?subtopic=guilds&page=view&GuildName={requests.utils.quote(name)}",
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
    page_text = soup.get_text().lower()
    if any(p in page_text for p in ["not found", "does not exist", "no guild", "nao encontrado"]):
        return None

    data = {"name": name, "found": False, "url": used_url}
    kv = _parse_table_kv(soup)

    for label, value in kv.items():
        if "founded" in label or "criada" in label or "fundada" in label:
            data["founded"] = value
        elif "description" in label or "descricao" in label or "descrição" in label:
            data["description"] = value[:200]
        elif "war" in label or "guerra" in label:
            data["war_status"] = value
        elif "leader" in label or "lider" in label or "líder" in label:
            data["leader"] = value
        elif "member" in label or "membro" in label:
            n = _extract_number(value)
            if n:
                data["member_count"] = n
        elif "world" in label or "servidor" in label:
            data["world"] = value
        elif "type" in label or "tipo" in label:
            data["guild_type"] = value
        elif "level" in label and "average" in label:
            data["avg_level"] = value

    # Extrair lista de membros da(s) tabela(s)
    members = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 3:
                name_cell = cells[0].get_text(strip=True)
                title_cell = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                voc_cell   = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                lvl_cell   = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                if name_cell and name_cell not in ("Name", "Nome", "Rank", ""):
                    members.append({
                        "name": name_cell,
                        "title": title_cell,
                        "vocation": voc_cell,
                        "level": _extract_number(lvl_cell),
                    })

    if members:
        data["members"] = members[:30]
        if not data.get("member_count"):
            data["member_count"] = len(members)
        data["found"] = True
    elif data.get("leader") or data.get("founded"):
        data["found"] = True

    if data["found"]:
        character_cache.set(cache_key, data, ttl_seconds=600)
        return data
    return None


# ── Guilds — listagem geral ───────────────────────────────────────────────────

def get_guilds_list() -> list[dict]:
    """Lista todas as guilds ativas do servidor."""
    cache_key = "guilds:list"
    cached = character_cache.get(cache_key)
    if cached:
        return cached

    urls_to_try = [
        f"{RUBINOT_BASE}/guilds",
        f"{RUBINOT_BASE}/?subtopic=guilds",
    ]

    resp = None
    for url in urls_to_try:
        resp = _get(url)
        if resp:
            break

    if not resp:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    guilds = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")[1:]
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2:
                name_cell    = cells[0].get_text(strip=True)
                members_cell = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                desc_cell    = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                if name_cell and name_cell not in ("Name", "Guild", "Nome", ""):
                    guilds.append({
                        "name": name_cell,
                        "members": _extract_number(members_cell),
                        "description": desc_cell[:100],
                    })
        if guilds:
            break

    if guilds:
        character_cache.set(cache_key, guilds, ttl_seconds=300)
    return guilds


# ── Mortes recentes ────────────────────────────────────────────────────────────

def get_recent_deaths(limit: int = 10) -> list[dict]:
    """Busca ultimas mortes (PvP kills) do servidor."""
    cache_key = "deaths:recent"
    cached = character_cache.get(cache_key)
    if cached:
        return cached

    urls_to_try = [
        f"{RUBINOT_BASE}/kills",
        f"{RUBINOT_BASE}/pvp",
        f"{RUBINOT_BASE}/latestkills",
        f"{RUBINOT_BASE}/?subtopic=latestkills",
    ]

    resp = None
    for url in urls_to_try:
        resp = _get(url)
        if resp:
            break

    if not resp:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    deaths = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")[1:]
        for row in rows[:limit]:
            cells = row.find_all("td")
            if len(cells) >= 2:
                killed   = cells[0].get_text(strip=True)
                killer   = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                time_str = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                if killed and killed not in ("Name", "Nome", "Killed", ""):
                    deaths.append({"killed": killed, "killer": killer, "time": time_str})
        if deaths:
            break

    if deaths:
        character_cache.set(cache_key, deaths, ttl_seconds=120)
    return deaths


# ── Highscores / Ranking ───────────────────────────────────────────────────────

VOC_HIGHSCORE_IDS = {
    "all": "0", "todas": "0",
    "knight": "2", "ek": "2",
    "paladin": "3", "rp": "3",
    "sorcerer": "4", "ms": "4",
    "druid": "5", "ed": "5",
    "monk": "6", "em": "6",
}

CATEGORY_IDS = {
    "level": "1", "nivel": "1",
    "magiclevel": "2", "ml": "2",
    "fist": "3",
    "club": "4",
    "sword": "5",
    "axe": "6",
    "dist": "7", "distance": "7",
    "shield": "8",
    "fishing": "9",
    "achievements": "10",
}


def get_highscores(vocation: str = "all", category: str = "level", limit: int = 10) -> list[dict]:
    """Busca ranking/highscores do Rubinot."""
    voc_id = VOC_HIGHSCORE_IDS.get(vocation.lower(), "0")
    cat_id = CATEGORY_IDS.get(category.lower(), "1")
    cache_key = f"hs:{voc_id}:{cat_id}"
    cached = character_cache.get(cache_key)
    if cached:
        return cached

    urls_to_try = [
        f"{RUBINOT_BASE}/highscores?category={cat_id}&vocation={voc_id}",
        f"{RUBINOT_BASE}/rankings?category={cat_id}&vocation={voc_id}",
        f"{RUBINOT_BASE}/?subtopic=highscores&category={cat_id}&vocation={voc_id}",
    ]

    resp = None
    for url in urls_to_try:
        resp = _get(url)
        if resp:
            break

    if not resp:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    entries = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")[1:]
        for row in rows[:limit]:
            cells = row.find_all("td")
            if len(cells) >= 3:
                rank  = cells[0].get_text(strip=True)
                name  = cells[1].get_text(strip=True)
                voc   = cells[2].get_text(strip=True)
                value = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                if name and name not in ("Name", "Nome", "Rank", ""):
                    entries.append({"rank": rank, "name": name, "vocation": voc, "value": value})
        if entries:
            break

    if entries:
        character_cache.set(cache_key, entries, ttl_seconds=300)
    return entries


# ── Noticias / News ────────────────────────────────────────────────────────────

def get_news(limit: int = 5) -> list[dict]:
    """Busca ultimas noticias/patches do servidor."""
    cache_key = "news:latest"
    cached = character_cache.get(cache_key)
    if cached:
        return cached

    urls_to_try = [
        f"{RUBINOT_BASE}/news",
        f"{RUBINOT_BASE}/newsnext",
        f"{RUBINOT_BASE}/?subtopic=news",
        f"{RUBINOT_BASE}/",
    ]

    resp = None
    for url in urls_to_try:
        resp = _get(url)
        if resp:
            break

    if not resp:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    news = []

    # Tenta encontrar artigos / posts de noticias
    # Padrao 1: tags article
    for article in soup.find_all("article")[:limit]:
        title_tag = article.find(["h1", "h2", "h3"])
        date_tag  = article.find(["time", "span"], class_=re.compile(r"date|time|data"))
        body_tag  = article.find(["p", "div"], class_=re.compile(r"body|content|text"))
        if title_tag:
            news.append({
                "title": title_tag.get_text(strip=True),
                "date": date_tag.get_text(strip=True) if date_tag else "",
                "body": body_tag.get_text(strip=True)[:300] if body_tag else "",
            })

    # Padrao 2: tabela de noticias
    if not news:
        for table in soup.find_all("table"):
            rows = table.find_all("tr")[1:]
            for row in rows[:limit]:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    title = cells[0].get_text(strip=True)
                    date  = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                    body  = cells[2].get_text(strip=True)[:300] if len(cells) > 2 else ""
                    if title and title not in ("Title", "Titulo", ""):
                        news.append({"title": title, "date": date, "body": body})
            if news:
                break

    # Padrao 3: divs com classes de noticia
    if not news:
        for div in soup.find_all("div", class_=re.compile(r"news|post|article|update"))[:limit]:
            title_tag = div.find(["h2", "h3", "h4", "strong"])
            if title_tag:
                news.append({
                    "title": title_tag.get_text(strip=True),
                    "date": "",
                    "body": div.get_text(strip=True)[:300],
                })

    if news:
        character_cache.set(cache_key, news, ttl_seconds=900)  # cache 15min
    return news


# ── Jogadores Online ──────────────────────────────────────────────────────────

def get_online_players() -> dict:
    """Busca numero e lista de jogadores online agora."""
    cache_key = "online:players"
    cached = character_cache.get(cache_key)
    if cached:
        return cached

    urls_to_try = [
        f"{RUBINOT_BASE}/online",
        f"{RUBINOT_BASE}/who",
        f"{RUBINOT_BASE}/?subtopic=whoisonline",
        f"{RUBINOT_BASE}/",  # homepage geralmente mostra contagem
    ]

    resp = None
    for url in urls_to_try:
        resp = _get(url)
        if resp:
            break

    if not resp:
        return {"count": 0, "players": []}

    soup = BeautifulSoup(resp.text, "html.parser")
    page_text = soup.get_text()

    # Tentar extrair contagem de online
    count = 0
    online_match = re.search(r"(\d+)\s*(?:players?\s+online|online|jogadores\s+online)", page_text, re.IGNORECASE)
    if online_match:
        count = int(online_match.group(1))

    players = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")[1:]
        for row in rows[:50]:
            cells = row.find_all("td")
            if len(cells) >= 2:
                name = cells[0].get_text(strip=True)
                level = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                voc = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                if name and name not in ("Name", "Nome", ""):
                    players.append({
                        "name": name,
                        "level": _extract_number(level),
                        "vocation": voc,
                    })
        if players:
            break

    if not count and players:
        count = len(players)

    result = {"count": count, "players": players}
    if count > 0 or players:
        character_cache.set(cache_key, result, ttl_seconds=60)  # cache 1min — muda rapido
    return result


# ── Status do servidor ────────────────────────────────────────────────────────

def get_server_status() -> dict:
    """Verifica se o servidor esta online e retorna status basico."""
    cache_key = "server:status"
    cached = character_cache.get(cache_key)
    if cached:
        return cached

    resp = _get(f"{RUBINOT_BASE}/")
    if not resp:
        return {"online": False, "message": "Site inacessivel"}

    soup = BeautifulSoup(resp.text, "html.parser")
    page_text = soup.get_text()

    status = {"online": True, "message": "Online"}

    # Tentar extrair informacoes de status da homepage
    online_match = re.search(r"(\d+)\s*(?:players?\s+online|jogadores\s+online|online)", page_text, re.IGNORECASE)
    if online_match:
        status["players_online"] = int(online_match.group(1))

    server_match = re.search(r"(?:server|servidor)\s+(?:status|estado)[:\s]+(\w+)", page_text, re.IGNORECASE)
    if server_match:
        status["server_status"] = server_match.group(1)

    uptime_match = re.search(r"uptime[:\s]+([\d\w\s]+)", page_text, re.IGNORECASE)
    if uptime_match:
        status["uptime"] = uptime_match.group(1).strip()[:50]

    character_cache.set(cache_key, status, ttl_seconds=120)
    return status


# ── Busca generica de personagens (autocomplete / sugestoes) ──────────────────

def search_characters(query: str, limit: int = 5) -> list[dict]:
    """Busca personagens por nome parcial — util para autocomplete."""
    cache_key = f"search:char:{query.lower()}"
    cached = character_cache.get(cache_key)
    if cached:
        return cached

    urls_to_try = [
        f"{RUBINOT_BASE}/characters?search={requests.utils.quote(query)}",
        f"{RUBINOT_BASE}/search?q={requests.utils.quote(query)}&type=character",
    ]

    resp = None
    for url in urls_to_try:
        resp = _get(url)
        if resp:
            break

    if not resp:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    for table in soup.find_all("table"):
        for row in table.find_all("tr")[1:limit + 1]:
            cells = row.find_all("td")
            if len(cells) >= 2:
                name  = cells[0].get_text(strip=True)
                level = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                voc   = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                if name:
                    results.append({"name": name, "level": _extract_number(level), "vocation": voc})
        if results:
            break

    if results:
        character_cache.set(cache_key, results, ttl_seconds=300)
    return results


# ── Formatos para Discord ─────────────────────────────────────────────────────

def format_character_embed(char: dict) -> dict:
    """Formata dados do personagem para Discord embed."""
    if not char.get("found"):
        return {
            "title": "Personagem nao encontrado",
            "description": f"O personagem **{char.get('name', '?')}** nao foi encontrado no Rubinot.",
        }

    name     = char.get("name_clean") or char.get("name", "?")
    level    = char.get("level", "?")
    vocation = char.get("vocation", "?")
    guild    = char.get("guild", "Sem guild")
    city     = char.get("city", "?")
    last_login = char.get("last_login", "?")

    voc_lower = str(vocation).lower()
    if "knight"   in voc_lower: emoji = "⚔️"
    elif "paladin" in voc_lower: emoji = "🏹"
    elif "druid"   in voc_lower: emoji = "🌿"
    elif "sorcerer" in voc_lower: emoji = "🔥"
    elif "monk"    in voc_lower: emoji = "🥊"
    else: emoji = "🎮"

    lines = [
        f"{emoji} **Vocacao:** {vocation}",
        f"⚡ **Nivel:** {level}",
        f"🏰 **Guild:** {guild}",
        f"🗺️ **Cidade:** {city}",
        f"🕐 **Ultimo login:** {last_login}",
    ]
    if char.get("achievement_points"):
        lines.append(f"🏆 **Achievement Points:** {char['achievement_points']}")
    if char.get("account_status"):
        lines.append(f"📋 **Conta:** {char['account_status']}")
    if char.get("charm_points"):
        lines.append(f"✨ **Charm Points:** {char['charm_points']}")

    return {
        "title": f"👤 {name}",
        "description": "\n".join(lines),
        "url": char.get("url", ""),
    }


def format_guild_embed(guild: dict) -> dict:
    """Formata dados da guild para Discord embed."""
    if not guild.get("found"):
        return {
            "title": "Guild nao encontrada",
            "description": f"A guild **{guild.get('name', '?')}** nao foi encontrada no Rubinot.",
        }
    name = guild.get("name", "?")
    lines = []
    if guild.get("leader"):
        lines.append(f"👑 **Lider:** {guild['leader']}")
    if guild.get("member_count"):
        lines.append(f"👥 **Membros:** {guild['member_count']}")
    if guild.get("founded"):
        lines.append(f"📅 **Fundada em:** {guild['founded']}")
    if guild.get("avg_level"):
        lines.append(f"📊 **Level medio:** {guild['avg_level']}")
    if guild.get("war_status"):
        lines.append(f"⚔️ **Status de guerra:** {guild['war_status']}")
    if guild.get("guild_type"):
        lines.append(f"🏷️ **Tipo:** {guild['guild_type']}")
    if guild.get("description"):
        lines.append(f"\n📝 {guild['description']}")
    if guild.get("members"):
        top = guild["members"][:8]
        member_lines = []
        for m in top:
            voc = m.get("vocation", "")[:2].upper()
            lvl = f" Lv{m['level']}" if m.get("level") else ""
            member_lines.append(f"{m['name']}{lvl}")
        lines.append(f"\n**Top membros:**\n" + " | ".join(member_lines))
    return {
        "title": f"🏰 Guild — {name}",
        "description": "\n".join(lines) or "Sem informacoes disponiveis.",
        "url": guild.get("url", ""),
    }


def format_deaths_embed(deaths: list[dict]) -> str:
    """Formata mortes recentes para Discord embed."""
    if not deaths:
        return "Sem mortes recentes ou pagina de kills indisponivel neste servidor."
    lines = ["**💀 Ultimas mortes no Rubinot**\n"]
    for d in deaths:
        killed   = d.get("killed", "?")
        killer   = d.get("killer", "?")
        t        = d.get("time", "")
        time_str = f" *({t})*" if t else ""
        lines.append(f"☠️ **{killed}** foi morto por **{killer}**{time_str}")
    return "\n".join(lines)


def format_highscores_embed(entries: list[dict], vocation: str, category: str) -> str:
    """Formata ranking para Discord embed."""
    if not entries:
        return "Nao foi possivel buscar o ranking. O site pode estar fora do ar."
    voc_label = vocation.upper() if vocation not in ("all", "todas") else "Todas as vocacoes"
    cat_label = category.capitalize()
    lines = [f"**🏆 Top {len(entries)} — {cat_label} | {voc_label}**\n"]
    medals = ["🥇", "🥈", "🥉"]
    for i, e in enumerate(entries):
        medal = medals[i] if i < 3 else f"`{e.get('rank', i+1)}.`"
        voc   = e.get("vocation", "")
        val   = e.get("value", "")
        lines.append(f"{medal} **{e['name']}** {voc} — {val}")
    return "\n".join(lines)


def format_news_embed(news: list[dict]) -> str:
    """Formata noticias para Discord embed."""
    if not news:
        return "Nao foi possivel carregar as noticias do servidor."
    lines = ["**📰 Ultimas noticias do Rubinot**\n"]
    for item in news:
        title = item.get("title", "Sem titulo")
        date  = item.get("date", "")
        body  = item.get("body", "")
        date_str = f" — *{date}*" if date else ""
        lines.append(f"**{title}**{date_str}")
        if body:
            lines.append(f"{body[:150]}...")
        lines.append("")
    return "\n".join(lines)[:3800]


def format_online_embed(data: dict) -> str:
    """Formata jogadores online para Discord embed."""
    count = data.get("count", 0)
    players = data.get("players", [])
    if not count and not players:
        return "Nao foi possivel verificar jogadores online."
    lines = [f"**🟢 Jogadores Online: {count}**\n"]
    if players:
        # Agrupa por vocacao
        by_voc: dict[str, list] = {}
        for p in players:
            voc = p.get("vocation", "Outro")
            by_voc.setdefault(voc, []).append(p)
        for voc, chars in sorted(by_voc.items()):
            names = ", ".join(c["name"] for c in chars[:10])
            lines.append(f"**{voc}** ({len(chars)}): {names}")
    return "\n".join(lines)[:3800]
