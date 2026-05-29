"""
Integração com TibiaWiki.dev (API gratuita, sem chave).
Fornece dados de itens e criaturas com imagens.
"""

import logging
import requests
from urllib.parse import quote
from cache import item_cache, creature_cache

logger = logging.getLogger(__name__)

TIBIAWIKI_API = "https://tibiawiki.dev/api"
# Imagem de item: usa Fandom Wiki como CDN (funciona como redirect público)
ITEM_IMAGE_URL = "https://tibia.fandom.com/wiki/Special:FilePath/{name}.gif"
CREATURE_IMAGE_URL = "https://tibia.fandom.com/wiki/Special:FilePath/{name}.gif"

_session = requests.Session()
_session.headers.update({
    "User-Agent": "CompanionTibia/1.0 (Discord Bot; Rubinot; por Soneca & Shawnks)",
    "Accept": "application/json",
})


def _api_get(endpoint: str) -> dict | None:
    """Faz GET na TibiaWiki.dev API com fallback SSL."""
    url = f"{TIBIAWIKI_API}/{endpoint}"
    try:
        resp = _session.get(url, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            return data if data else None
        logger.warning("TibiaWiki API %s → %s", url, resp.status_code)
    except Exception as e:
        # Fallback SSL para proxies corporativos
        if "SSL" in str(e) or "certificate" in str(e).lower():
            try:
                resp = _session.get(url, timeout=6, verify=False)
                if resp.status_code == 200:
                    data = resp.json()
                    return data if data else None
            except Exception:
                pass
        logger.error("TibiaWiki API erro: %s", e)
    return None


def get_item(name: str) -> dict | None:
    """
    Busca dados de um item na TibiaWiki.dev.
    Retorna dict com armor, weight, slots de imbue, quem vende, etc.
    """
    cache_key = f"item:{name.lower()}"
    cached = item_cache.get(cache_key)
    if cached:
        return cached

    data = _api_get(f"items/{quote(name)}")
    if data and data.get("name"):
        # Adiciona URL da imagem
        img_name = data["name"].replace(" ", "_")
        data["image_url"] = ITEM_IMAGE_URL.format(name=quote(img_name))
        item_cache.set(cache_key, data, ttl_seconds=3600)
        return data

    return None


def get_creature(name: str) -> dict | None:
    """
    Busca dados de uma criatura na TibiaWiki.dev.
    Retorna HP, EXP, loot, resistências, etc.
    """
    cache_key = f"creature:{name.lower()}"
    cached = creature_cache.get(cache_key)
    if cached:
        return cached

    data = _api_get(f"creatures/{quote(name)}")
    if data and data.get("name"):
        img_name = data["name"].replace(" ", "_")
        data["image_url"] = CREATURE_IMAGE_URL.format(name=quote(img_name))
        creature_cache.set(cache_key, data, ttl_seconds=3600)
        return data

    return None


def format_item_embed(item: dict) -> dict:
    """Formata dados do item para Discord embed."""
    name = item.get("name", "?")
    lines = []

    if item.get("armor"):
        lines.append(f"🛡️ **Armor:** {item['armor']}")
    if item.get("attack"):
        lines.append(f"⚔️ **Ataque:** {item['attack']}")
    if item.get("defense"):
        lines.append(f"🔰 **Defesa:** {item['defense']}")
    if item.get("weight"):
        lines.append(f"⚖️ **Peso:** {item['weight']} oz")
    if item.get("imbueslots"):
        lines.append(f"💎 **Slots de Imbue:** {item['imbueslots']}")
    if item.get("slot"):
        lines.append(f"📦 **Slot:** {item['slot']}")
    if item.get("vocrequired"):
        lines.append(f"🎭 **Vocação:** {item['vocrequired']}")
    if item.get("levelrequired"):
        lines.append(f"📊 **Nível mínimo:** {item['levelrequired']}")
    if item.get("value"):
        try:
            lines.append(f"💰 **Valor NPC:** {int(item['value']):,} gp")
        except (ValueError, TypeError):
            lines.append(f"💰 **Valor NPC:** {item['value']} gp")
    if item.get("buyfrom"):
        buy = item["buyfrom"]
        if isinstance(buy, list):
            buy = ", ".join(buy[:3])
        lines.append(f"🛒 **Comprar em:** {buy}")
    if item.get("droppedby"):
        dropped = item["droppedby"]
        if isinstance(dropped, list):
            dropped = ", ".join(dropped[:5])
        lines.append(f"🎯 **Dropado por:** {dropped}")
    if item.get("notes"):
        notes = str(item["notes"])[:200]
        lines.append(f"\n📝 {notes}")

    return {
        "title": f"📦 {name}",
        "description": "\n".join(lines) if lines else "Dados não disponíveis.",
        "thumbnail_url": item.get("image_url"),
    }


def format_creature_embed(creature: dict) -> dict:
    """Formata dados da criatura para Discord embed."""
    name = creature.get("name", "?")
    lines = []

    if creature.get("hp"):
        lines.append(f"❤️ **HP:** {creature['hp']:,}" if isinstance(creature['hp'], int) else f"❤️ **HP:** {creature['hp']}")
    if creature.get("exp"):
        lines.append(f"✨ **EXP:** {creature['exp']:,}" if isinstance(creature['exp'], int) else f"✨ **EXP:** {creature['exp']}")
    if creature.get("maxdmg"):
        lines.append(f"⚔️ **Dano máximo:** {creature['maxdmg']}")
    if creature.get("armor"):
        lines.append(f"🛡️ **Armor:** {creature['armor']}")
    if creature.get("speed"):
        lines.append(f"💨 **Velocidade:** {creature['speed']}")

    # Resistências
    resist_lines = []
    resist_map = {
        "physicalDmgMod": "Físico",
        "fireDmgMod": "Fogo",
        "iceDmgMod": "Gelo",
        "energyDmgMod": "Energia",
        "earthDmgMod": "Terra",
        "deathDmgMod": "Morte",
        "holyDmgMod": "Santo",
    }
    for key, label in resist_map.items():
        val = creature.get(key)
        if val and val not in ("0%", "100%", 0, 100):
            resist_lines.append(f"{label}: {val}")
    if resist_lines:
        lines.append(f"\n🔰 **Resistências:** {' | '.join(resist_lines)}")

    # Imunidades
    immunities = []
    if creature.get("paraimmune") == "1":
        immunities.append("Paralyze")
    if creature.get("senseinvis") == "1":
        immunities.append("Vê Invisível")
    if immunities:
        lines.append(f"🚫 **Imune a:** {', '.join(immunities)}")

    # Loot (top 8)
    if creature.get("loot") and isinstance(creature["loot"], list):
        loot_items = creature["loot"][:8]
        loot_text = []
        for entry in loot_items:
            if isinstance(entry, dict):
                item_name = entry.get("item") or entry.get("name", "")
                amount = entry.get("amount", "")
                rarity = entry.get("rarity", "")
                if item_name:
                    part = item_name
                    if amount and amount != "1":
                        part += f" x{amount}"
                    if rarity:
                        part += f" *({rarity})*"
                    loot_text.append(part)
            elif isinstance(entry, str):
                loot_text.append(entry)
        if loot_text:
            lines.append(f"\n🎁 **Loot:** {', '.join(loot_text)}")

    if creature.get("location"):
        loc = str(creature["location"])[:150]
        lines.append(f"\n📍 **Localização:** {loc}")

    return {
        "title": f"👾 {name}",
        "description": "\n".join(lines) if lines else "Dados não disponíveis.",
        "thumbnail_url": creature.get("image_url"),
    }
