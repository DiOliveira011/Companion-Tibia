"""
Integração com YouTube Data API v3 (gratuita — 10.000 unidades/dia).
Busca vídeos de hunt relevantes para enriquecer as respostas do bot.
Só funciona se YOUTUBE_API_KEY estiver configurado — silenciosa se não estiver.
"""

import os
import logging
import requests
from cache import TTLCache
from urllib.parse import quote

logger = logging.getLogger(__name__)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

_cache = TTLCache()   # TTL 2h — resultados de busca mudam pouco
AVAILABLE = bool(YOUTUBE_API_KEY)


def search_hunt_videos(hunt_name: str, vocation: str = "", max_results: int = 3) -> list[dict]:
    """
    Busca vídeos de hunt no YouTube.

    Args:
        hunt_name: nome do spot (ex: "Demon Forge", "Asura Mirror")
        vocation: vocação para refinar a busca (ex: "EK", "Monk")
        max_results: número máximo de vídeos (padrão 3)

    Returns:
        Lista de dicts com: title, url, channel, thumbnail
    """
    if not AVAILABLE:
        return []

    query = f"Tibia OT {hunt_name}"
    if vocation:
        query += f" {vocation}"
    query += " Rubinot hunt guide"

    cache_key = f"yt:{query.lower().replace(' ', '_')}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "relevanceLanguage": "pt",
            "key": YOUTUBE_API_KEY,
            "videoEmbeddable": "true",
            "safeSearch": "none",
        }
        resp = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=6)
        resp.raise_for_status()
        data = resp.json()

        videos = []
        for item in data.get("items", []):
            video_id = item["id"].get("videoId")
            snippet = item.get("snippet", {})
            if video_id:
                videos.append({
                    "title": snippet.get("title", "Sem título"),
                    "url": f"https://youtu.be/{video_id}",
                    "channel": snippet.get("channelTitle", ""),
                    "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
                })

        _cache.set(cache_key, videos, ttl_seconds=7200)
        return videos

    except requests.HTTPError as e:
        if "quotaExceeded" in str(e):
            logger.warning("YouTube API: cota diária atingida (10k/dia). Tente amanhã.")
        else:
            logger.warning("YouTube API erro: %s", e)
    except Exception as e:
        logger.warning("YouTube API erro: %s", e)

    return []


def format_videos_field(videos: list[dict]) -> str:
    """Formata lista de vídeos para campo em Discord embed."""
    if not videos:
        return ""
    lines = []
    for v in videos:
        channel = f" • {v['channel']}" if v.get("channel") else ""
        lines.append(f"🎬 [{v['title'][:60]}]({v['url']}){channel}")
    return "\n".join(lines)


def search_vocation_guide(vocation: str, max_results: int = 2) -> list[dict]:
    """Busca guias de vocação no YouTube."""
    return search_hunt_videos(f"{vocation} guide leveling", max_results=max_results)
