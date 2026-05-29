"""
Companion Tibia — Bot Discord v3.0
Rubinot Open PvP Server
Idealizado e desenvolvido por Soneca e Shawnks

Novidades v3:
- Memória persistente entre reinicializações (memory.py)
- Modo dual IA: Groq (free) + Claude opcional (ai_client.py)
- YouTube API: vídeos de hunt automáticos (youtube_api.py)
- /guild, /mortes, /ranking (scraper.py expandido)
- /forum: busca em OtLand + DuckDuckGo (forum_scraper.py)
- /modelo: troca de IA por sessão
- /perfil: salva vocação, nível e personagem
- KB extra via GitHub (kb_loader.py)
"""

import os
import asyncio
import logging
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# Módulos do projeto
from keep_alive import start_keep_alive
from knowledge_base import (
    SYSTEM_PROMPT, FOOTER_TEXT, VOCATION_ALIASES, VOCATION_EMOJIS, HELP_TEXT
)
from scraper import (
    get_character, get_party_data, format_character_embed,
    get_guild, format_guild_embed,
    get_guilds_list,
    get_recent_deaths, format_deaths_embed,
    get_highscores, format_highscores_embed,
    get_news, format_news_embed,
    get_online_players, format_online_embed,
    get_server_status,
)
from tibia_api import get_item, get_creature, format_item_embed, format_creature_embed
from memory import (
    get_history, add_message, clear_history,
    get_profile, update_profile, get_preferred_ai, set_preferred_ai,
    build_profile_context, count_users,
)
from ai_client import chat as ai_chat, status_text as ai_status, CLAUDE_AVAILABLE
from youtube_api import search_hunt_videos, format_videos_field, AVAILABLE as YT_AVAILABLE
from forum_scraper import search_forum, format_forum_results
from kb_loader import build_full_system_prompt, reload_kb, kb_status
from wiki_scraper import (
    search_wiki, get_wiki_page, get_quest_info, get_boss_info,
    get_linked_tasks, get_soulpit_info,
    format_wiki_result, format_search_results,
)

# ── Configuração ──────────────────────────────────────────────────────────────

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("companion_tibia")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_system_prompt() -> str:
    """Retorna system prompt completo (base + extra GitHub se configurado)."""
    return build_full_system_prompt(SYSTEM_PROMPT)


def ask_ai(user_id: int, question: str, extra_context: str = "") -> tuple[str, str]:
    """
    Envia pergunta para a IA preferida do usuário.
    Injeta perfil do jogador + histórico de conversa.
    Retorna (resposta, modelo_usado).
    """
    history   = get_history(user_id)
    profile_ctx = build_profile_context(user_id)
    preferred = get_preferred_ai(user_id)
    system    = get_system_prompt()

    prompt = question
    if extra_context:
        prompt = f"{extra_context}\n\n{question}"
    if profile_ctx:
        prompt = f"{profile_ctx}\n\n{prompt}"

    messages = history + [{"role": "user", "content": prompt}]
    answer, model = ai_chat(messages, system, preferred=preferred)

    add_message(user_id, "user", question)
    add_message(user_id, "assistant", answer)
    return answer, model


def make_embed(
    title: str,
    description: str,
    color: int = 0xC8A951,
    thumbnail_url: str = None,
    url: str = None,
    model: str = None,
) -> discord.Embed:
    embed = discord.Embed(title=title, description=description[:4000], color=color)
    footer = FOOTER_TEXT
    if model:
        footer += f" • {model}"
    embed.set_footer(text=footer)
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    if url:
        embed.url = url
    return embed


async def run(func, *args):
    """Atalho para executar função síncrona fora do event loop."""
    return await asyncio.get_event_loop().run_in_executor(None, func, *args)


# ── Eventos ───────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    await tree.sync()
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name="Rubinot Open PvP | /ajuda"
        )
    )
    logger.info("✅ Companion Tibia v3.0 online como %s", bot.user)
    logger.info("   Claude disponível: %s", CLAUDE_AVAILABLE)
    logger.info("   YouTube disponível: %s", YT_AVAILABLE)
    logger.info("   Usuários com memória: %d", count_users())


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    await bot.process_commands(message)
    if bot.user in message.mentions:
        question = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not question:
            await message.reply("👋 Oi! Pode me perguntar qualquer coisa sobre o Rubinot.\nUse `/ajuda` para ver os comandos.")
            return
        async with message.channel.typing():
            answer, model = await run(ask_ai, message.author.id, question)
        embed = make_embed("🏹 Companion Tibia", answer, model=model)
        await message.reply(embed=embed)


# ── Comandos — Informação ─────────────────────────────────────────────────────

@tree.command(name="ajuda", description="Lista todos os comandos do Companion Tibia")
async def ajuda(interaction: discord.Interaction):
    embed = make_embed("📖 Companion Tibia — Ajuda", HELP_TEXT, color=0x5865F2)
    embed.set_author(name="Companion Tibia", icon_url=interaction.client.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)


@tree.command(name="ask", description="Pergunta livre sobre qualquer coisa do Tibia/Rubinot")
@app_commands.describe(pergunta="Sua pergunta sobre o jogo")
async def ask(interaction: discord.Interaction, pergunta: str):
    await interaction.response.defer()
    answer, model = await run(ask_ai, interaction.user.id, pergunta)
    embed = make_embed(f"💬 {interaction.user.display_name} perguntou:", answer, model=model)
    await interaction.followup.send(embed=embed)


@tree.command(name="hunt", description="Melhores hunts para sua vocação e nível")
@app_commands.describe(vocacao="Sua vocação", nivel="Seu nível atual", modo="Solo, duo ou party")
@app_commands.choices(
    vocacao=[
        app_commands.Choice(name="⚔️ Knight (EK)",   value="knight"),
        app_commands.Choice(name="🏹 Paladin (RP)",  value="paladin"),
        app_commands.Choice(name="🌿 Druid (ED)",    value="druid"),
        app_commands.Choice(name="🔥 Sorcerer (MS)", value="sorcerer"),
        app_commands.Choice(name="🥊 Monk (EM)",     value="monk"),
    ],
    modo=[
        app_commands.Choice(name="Solo",       value="solo"),
        app_commands.Choice(name="Duo",        value="duo"),
        app_commands.Choice(name="Party (3-5)", value="party"),
        app_commands.Choice(name="Qualquer",   value="qualquer"),
    ]
)
async def hunt(
    interaction: discord.Interaction,
    vocacao: str,
    nivel: int,
    modo: app_commands.Choice[str] = None,
):
    await interaction.response.defer()
    modo_texto = f" modo {modo.value}" if modo else ""
    emoji    = VOCATION_EMOJIS.get(vocacao, "🗡️")
    voc_nome = VOCATION_ALIASES.get(vocacao, vocacao)
    pergunta = (
        f"Liste as 4 melhores hunts para {voc_nome} nível {nivel}{modo_texto} no Rubinot. "
        f"Para cada uma: nome do spot, exp/h estimado, como chegar, estratégia/rotação de spells, "
        f"imbue recomendado e loot destaque."
    )
    answer, model = await run(ask_ai, interaction.user.id, pergunta)
    embed = make_embed(f"{emoji} Hunt — {voc_nome} Nível {nivel}", answer, model=model)

    # Adicionar vídeos do YouTube se disponível
    if YT_AVAILABLE:
        videos = await run(search_hunt_videos, f"Tibia {voc_nome} nivel {nivel}", vocacao, 3)
        if videos:
            embed.add_field(
                name="🎬 Vídeos relacionados",
                value=format_videos_field(videos),
                inline=False
            )

    await interaction.followup.send(embed=embed)


@tree.command(name="vocacao", description="Guia completo de uma vocação")
@app_commands.describe(vocacao="Escolha a vocação")
@app_commands.choices(vocacao=[
    app_commands.Choice(name="⚔️ Knight (EK)",   value="knight"),
    app_commands.Choice(name="🏹 Paladin (RP)",  value="paladin"),
    app_commands.Choice(name="🌿 Druid (ED)",    value="druid"),
    app_commands.Choice(name="🔥 Sorcerer (MS)", value="sorcerer"),
    app_commands.Choice(name="🥊 Monk (EM)",     value="monk"),
])
async def vocacao(interaction: discord.Interaction, vocacao: str):
    await interaction.response.defer()
    emoji    = VOCATION_EMOJIS.get(vocacao, "🗡️")
    voc_nome = VOCATION_ALIASES.get(vocacao, vocacao)
    pergunta = (
        f"Guia completo de {voc_nome} no Rubinot: papel no grupo, pontos fortes e fracos, "
        f"build por fase (early/mid/end), rotação de spells principal, imbues prioritários e dica mais importante."
    )
    answer, model = await run(ask_ai, interaction.user.id, pergunta)
    embed = make_embed(f"{emoji} {voc_nome} — Guia Completo", answer, model=model)
    await interaction.followup.send(embed=embed)


@tree.command(name="spells", description="Rotação de spells recomendada")
@app_commands.describe(vocacao="Sua vocação", situacao="Contexto: solo hunt, party healer, boss…")
@app_commands.choices(vocacao=[
    app_commands.Choice(name="⚔️ Knight (EK)",   value="knight"),
    app_commands.Choice(name="🏹 Paladin (RP)",  value="paladin"),
    app_commands.Choice(name="🌿 Druid (ED)",    value="druid"),
    app_commands.Choice(name="🔥 Sorcerer (MS)", value="sorcerer"),
    app_commands.Choice(name="🥊 Monk (EM)",     value="monk"),
])
async def spells(interaction: discord.Interaction, vocacao: str, situacao: str = "hunt solo"):
    await interaction.response.defer()
    emoji    = VOCATION_EMOJIS.get(vocacao, "🗡️")
    voc_nome = VOCATION_ALIASES.get(vocacao, vocacao)
    pergunta = (
        f"Rotação de spells ideal para {voc_nome} em {situacao}. "
        f"Liste em ordem de prioridade com nome, comando e função."
    )
    answer, model = await run(ask_ai, interaction.user.id, pergunta)
    embed = make_embed(f"{emoji} Spells — {voc_nome} ({situacao})", answer, model=model)
    await interaction.followup.send(embed=embed)


@tree.command(name="nivel", description="O que fazer no seu nível atual")
@app_commands.describe(vocacao="Sua vocação", nivel="Seu nível atual")
@app_commands.choices(vocacao=[
    app_commands.Choice(name="⚔️ Knight (EK)",   value="knight"),
    app_commands.Choice(name="🏹 Paladin (RP)",  value="paladin"),
    app_commands.Choice(name="🌿 Druid (ED)",    value="druid"),
    app_commands.Choice(name="🔥 Sorcerer (MS)", value="sorcerer"),
    app_commands.Choice(name="🥊 Monk (EM)",     value="monk"),
])
async def nivel_cmd(interaction: discord.Interaction, vocacao: str, nivel: int):
    await interaction.response.defer()
    emoji    = VOCATION_EMOJIS.get(vocacao, "🗡️")
    voc_nome = VOCATION_ALIASES.get(vocacao, vocacao)
    pergunta = (
        f"Sou {voc_nome} nível {nivel} no Rubinot. "
        f"1) Hunt principal agora, 2) Equipamento necessário, 3) Próximo upgrade, "
        f"4) Spell/mecânica a dominar, 5) Quest disponível no meu nível."
    )
    answer, model = await run(ask_ai, interaction.user.id, pergunta)
    embed = make_embed(f"{emoji} Roadmap — {voc_nome} Nível {nivel}", answer, model=model)
    await interaction.followup.send(embed=embed)


@tree.command(name="imbue", description="Melhores imbuements para sua vocação")
@app_commands.describe(vocacao="Sua vocação", slot="Slot do equipamento")
@app_commands.choices(
    vocacao=[
        app_commands.Choice(name="⚔️ Knight (EK)",   value="knight"),
        app_commands.Choice(name="🏹 Paladin (RP)",  value="paladin"),
        app_commands.Choice(name="🌿 Druid (ED)",    value="druid"),
        app_commands.Choice(name="🔥 Sorcerer (MS)", value="sorcerer"),
        app_commands.Choice(name="🥊 Monk (EM)",     value="monk"),
    ],
    slot=[
        app_commands.Choice(name="Arma",          value="arma"),
        app_commands.Choice(name="Capacete",      value="capacete"),
        app_commands.Choice(name="Armadura",      value="armadura"),
        app_commands.Choice(name="Todos os slots", value="todos os slots"),
    ]
)
async def imbue(interaction: discord.Interaction, vocacao: str, slot: str = "todos os slots"):
    await interaction.response.defer()
    emoji    = VOCATION_EMOJIS.get(vocacao, "🗡️")
    voc_nome = VOCATION_ALIASES.get(vocacao, vocacao)
    pergunta = (
        f"Melhores imbuements para {voc_nome} no slot {slot}. "
        f"Liste em ordem de prioridade com efeito e justificativa."
    )
    answer, model = await run(ask_ai, interaction.user.id, pergunta)
    embed = make_embed(f"💎 Imbues — {voc_nome} ({slot})", answer, model=model)
    await interaction.followup.send(embed=embed)


@tree.command(name="grupo", description="Analisa composição de party")
@app_commands.describe(composicao="Ex: EK 200, ED 180, MS 150")
async def grupo(interaction: discord.Interaction, composicao: str):
    await interaction.response.defer()
    pergunta = (
        f"Analise a composição de grupo: {composicao}. "
        f"1) É uma boa composição? 2) Papel de cada um, 3) Melhor hunt, "
        f"4) Ponto fraco, 5) Ajuste recomendado."
    )
    answer, model = await run(ask_ai, interaction.user.id, pergunta)
    embed = make_embed("👥 Análise de Grupo", answer, model=model)
    await interaction.followup.send(embed=embed)


# ── Comandos — Dados do Rubinot ───────────────────────────────────────────────

@tree.command(name="personagem", description="Busca dados de um personagem no Rubinot")
@app_commands.describe(nome="Nome exato do personagem (case sensitive)")
async def personagem(interaction: discord.Interaction, nome: str):
    await interaction.response.defer()
    char_data = await run(get_character, nome)
    if not char_data or not char_data.get("found"):
        embed = make_embed(
            "❌ Personagem não encontrado",
            f"**{nome}** não foi encontrado.\nVerifique o nome (case sensitive).\n"
            f"🔗 [Buscar no site](<https://rubinot.com.br/characters?name={nome.replace(' ', '+')}>)",
            color=0xE74C3C,
        )
        await interaction.followup.send(embed=embed)
        return

    embed_data = format_character_embed(char_data)
    embed = make_embed(embed_data["title"], embed_data["description"], color=0x2ECC71, url=embed_data.get("url"))

    if char_data.get("level") and char_data.get("vocation"):
        ia_tip, _ = await run(
            ask_ai, interaction.user.id,
            f"Personagem {nome}: {char_data['vocation']} nível {char_data['level']} no Rubinot. "
            f"Em 2 linhas: melhor hunt agora e próximo upgrade."
        )
        embed.add_field(name="💡 Dica do Companion", value=ia_tip[:400], inline=False)

    # Salva perfil do usuário automaticamente
    update_profile(
        interaction.user.id,
        char_name=nome,
        vocation=char_data.get("vocation"),
        level=char_data.get("level"),
    )
    await interaction.followup.send(embed=embed)


@tree.command(name="party", description="Busca dados reais de até 5 personagens e analisa o grupo")
@app_commands.describe(nomes="Nomes separados por vírgula. Ex: Soneca, Shawnks, Fulano")
async def party(interaction: discord.Interaction, nomes: str):
    await interaction.response.defer()
    name_list = [n.strip() for n in nomes.split(",") if n.strip()][:5]
    if not name_list:
        await interaction.followup.send("❌ Informe ao menos um nome.")
        return

    chars = await run(get_party_data, name_list)
    found     = [c for c in chars if c.get("found")]
    not_found = [c for c in chars if not c.get("found")]

    lines = []
    party_summary = []
    for c in found:
        name = c.get("name_clean") or c.get("name", "?")
        lvl  = c.get("level", "?")
        voc  = c.get("vocation", "?")
        emoji = ("⚔️" if "knight" in str(voc).lower() else
                 "🏹" if "paladin" in str(voc).lower() else
                 "🌿" if "druid"   in str(voc).lower() else
                 "🔥" if "sorcerer" in str(voc).lower() else
                 "🥊" if "monk"    in str(voc).lower() else "🎮")
        lines.append(f"{emoji} **{name}** — {voc} Lv.{lvl}")
        party_summary.append(f"{voc} {lvl}")
    for c in not_found:
        lines.append(f"❌ **{c.get('name', '?')}** — não encontrado")

    if not found:
        await interaction.followup.send(embed=make_embed("👥 Nenhum personagem encontrado",
            "Verifique os nomes (case sensitive no Rubinot).", color=0xE74C3C))
        return

    desc = "\n".join(lines)
    if party_summary:
        ia_q = (
            f"Analise esta party do Rubinot com dados reais: {', '.join(party_summary)}. "
            f"Sinergia, melhor hunt, papel de cada um, ponto fraco, dica."
        )
        ia_analysis, model = await run(ask_ai, interaction.user.id, ia_q)
        desc += f"\n\n**💡 Análise:**\n{ia_analysis[:700]}"
    else:
        model = None

    embed = make_embed("👥 Party — Dados do Rubinot", desc, color=0x9B59B6, model=model)
    await interaction.followup.send(embed=embed)


@tree.command(name="guild", description="Dados de uma guild no Rubinot")
@app_commands.describe(nome="Nome exato da guild")
async def guild_cmd(interaction: discord.Interaction, nome: str):
    await interaction.response.defer()
    guild_data = await run(get_guild, nome)
    if not guild_data or not guild_data.get("found"):
        embed = make_embed(
            "❌ Guild não encontrada",
            f"**{nome}** não foi encontrada.\n"
            f"🔗 [Buscar no site](<https://rubinot.com.br/?subtopic=guilds>)",
            color=0xE74C3C,
        )
        await interaction.followup.send(embed=embed)
        return

    embed_data = format_guild_embed(guild_data)
    embed = make_embed(embed_data["title"], embed_data["description"], color=0xF39C12, url=embed_data.get("url"))
    await interaction.followup.send(embed=embed)


@tree.command(name="mortes", description="Últimas mortes (PvP kills) no Rubinot em tempo real")
async def mortes(interaction: discord.Interaction):
    await interaction.response.defer()
    deaths = await run(get_recent_deaths, 12)
    desc = format_deaths_embed(deaths)
    embed = make_embed("💀 Mortes Recentes — Rubinot", desc, color=0x8B0000)
    await interaction.followup.send(embed=embed)


@tree.command(name="ranking", description="Top players do Rubinot por vocação e categoria")
@app_commands.describe(
    vocacao="Filtrar por vocação (padrão: todas)",
    categoria="Categoria do ranking (padrão: level)"
)
@app_commands.choices(
    vocacao=[
        app_commands.Choice(name="🌐 Todas",          value="all"),
        app_commands.Choice(name="⚔️ Knight (EK)",   value="knight"),
        app_commands.Choice(name="🏹 Paladin (RP)",  value="paladin"),
        app_commands.Choice(name="🌿 Druid (ED)",    value="druid"),
        app_commands.Choice(name="🔥 Sorcerer (MS)", value="sorcerer"),
        app_commands.Choice(name="🥊 Monk (EM)",     value="monk"),
    ],
    categoria=[
        app_commands.Choice(name="Nível",          value="level"),
        app_commands.Choice(name="Magic Level",    value="magiclevel"),
        app_commands.Choice(name="Achievements",   value="achievements"),
        app_commands.Choice(name="Sword Fighting", value="sword"),
        app_commands.Choice(name="Axe Fighting",   value="axe"),
        app_commands.Choice(name="Club Fighting",  value="club"),
        app_commands.Choice(name="Fist Fighting",  value="fist"),
        app_commands.Choice(name="Distance",       value="dist"),
        app_commands.Choice(name="Shielding",      value="shield"),
    ]
)
async def ranking(
    interaction: discord.Interaction,
    vocacao: str = "all",
    categoria: str = "level",
):
    await interaction.response.defer()
    entries = await run(get_highscores, vocacao, categoria, 10)
    desc    = format_highscores_embed(entries, vocacao, categoria)
    embed   = make_embed("🏆 Ranking — Rubinot Open PvP", desc, color=0xF1C40F)
    await interaction.followup.send(embed=embed)


# ── Comandos — Tibia Wiki ─────────────────────────────────────────────────────

@tree.command(name="item", description="Info de um item do Tibia (stats + imagem)")
@app_commands.describe(nome="Nome em inglês. Ex: Dragon Scale Mail")
async def item_cmd(interaction: discord.Interaction, nome: str):
    await interaction.response.defer()
    item_data = await run(get_item, nome)
    if not item_data:
        answer, model = await run(ask_ai, interaction.user.id,
            f"Info sobre o item '{nome}': stats, onde dropar, quem vende, para qual vocação serve.")
        await interaction.followup.send(embed=make_embed(f"📦 {nome}", answer, model=model))
        return
    embed_data = format_item_embed(item_data)
    embed = make_embed(embed_data["title"], embed_data["description"], color=0xF39C12, thumbnail_url=embed_data.get("thumbnail_url"))
    ia_tip, _ = await run(ask_ai, interaction.user.id,
        f"Em 1 linha: para qual vocação o '{item_data.get('name', nome)}' é mais útil no Rubinot?")
    if ia_tip:
        embed.add_field(name="💡 Dica de uso", value=ia_tip[:250], inline=False)
    await interaction.followup.send(embed=embed)


@tree.command(name="monstro", description="Stats e loot de uma criatura do Tibia")
@app_commands.describe(nome="Nome em inglês. Ex: Dragon Lord")
async def monstro(interaction: discord.Interaction, nome: str):
    await interaction.response.defer()
    creature_data = await run(get_creature, nome)
    if not creature_data:
        answer, model = await run(ask_ai, interaction.user.id,
            f"Info sobre a criatura '{nome}': HP, EXP, loot, fraquezas, onde caçar.")
        await interaction.followup.send(embed=make_embed(f"👾 {nome}", answer, model=model))
        return
    embed_data = format_creature_embed(creature_data)
    embed = make_embed(embed_data["title"], embed_data["description"], color=0xE74C3C, thumbnail_url=embed_data.get("thumbnail_url"))
    ia_tip, _ = await run(ask_ai, interaction.user.id,
        f"Em 2 linhas: qual vocação caça melhor '{creature_data.get('name', nome)}' e qual a fraqueza elemental?")
    if ia_tip:
        embed.add_field(name="💡 Melhor para caçar", value=ia_tip[:250], inline=False)
    await interaction.followup.send(embed=embed)


# ── Comandos — Guias ──────────────────────────────────────────────────────────

@tree.command(name="boss", description="Guia de um boss do Rubinot")
@app_commands.describe(nome="Ex: Ferumbras, Orshabaal, Gaz'haragoth")
async def boss(interaction: discord.Interaction, nome: str):
    await interaction.response.defer()
    pergunta = (
        f"Guia do boss '{nome}' no Rubinot: nível mínimo, composição ideal, "
        f"estratégia, ataques a evitar, loot destaque, dica de sobrevivência."
    )
    answer, model = await run(ask_ai, interaction.user.id, pergunta)
    embed = make_embed(f"💀 Boss — {nome}", answer, color=0x8B0000, model=model)
    await interaction.followup.send(embed=embed)


@tree.command(name="quest", description="Guia de uma quest do Rubinot")
@app_commands.describe(nome="Ex: Soul War, Inquisition, Ferumbras Ascendant")
async def quest(interaction: discord.Interaction, nome: str):
    await interaction.response.defer()
    pergunta = (
        f"Guia da quest '{nome}' no Rubinot: nível mínimo, vocações recomendadas, "
        f"passo a passo resumido, recompensas principais, dica mais importante."
    )
    answer, model = await run(ask_ai, interaction.user.id, pergunta)
    embed = make_embed(f"📜 Quest — {nome}", answer, color=0x27AE60, model=model)
    await interaction.followup.send(embed=embed)


@tree.command(name="rubinot", description="Info sobre o servidor Rubinot")
@app_commands.describe(tema="Ex: forge, transfer, soulpit, castle, VIP, linked tasks")
async def rubinot(interaction: discord.Interaction, tema: str = "sistemas gerais"):
    await interaction.response.defer()
    pergunta = f"Explique sobre '{tema}' no Rubinot. Seja direto e dê dados concretos."
    answer, model = await run(ask_ai, interaction.user.id, pergunta)
    embed = make_embed("🏰 Rubinot Open PvP", answer, color=0xE74C3C, model=model)
    await interaction.followup.send(embed=embed)


@tree.command(name="forum", description="Busca guias e discussões no fórum OtLand sobre Rubinot")
@app_commands.describe(busca="O que quer buscar. Ex: monk build, EK hunt 200, Cobra quest")
async def forum(interaction: discord.Interaction, busca: str):
    await interaction.response.defer()
    results = await run(search_forum, busca, 5)
    if not results:
        # Fallback: responder com IA
        answer, model = await run(ask_ai, interaction.user.id,
            f"O que a comunidade comenta sobre '{busca}' no Rubinot? Dê um resumo baseado no que você sabe.")
        embed = make_embed(f"🌐 Fórum — {busca}", answer, model=model)
        await interaction.followup.send(embed=embed)
        return
    desc = format_forum_results(results, f"Resultados para: {busca}")
    embed = make_embed("🌐 Fórum — OtLand / Rubinot", desc, color=0x3498DB)
    embed.set_footer(text=f"{FOOTER_TEXT} • Fonte: OtLand.net")
    await interaction.followup.send(embed=embed)


# ── Comandos — Perfil & IA ────────────────────────────────────────────────────

@tree.command(name="perfil", description="Salva seu personagem, vocação e nível para respostas personalizadas")
@app_commands.describe(
    char_name="Seu nome no Rubinot",
    vocacao="Sua vocação",
    nivel="Seu nível atual"
)
@app_commands.choices(vocacao=[
    app_commands.Choice(name="⚔️ Knight (EK)",   value="knight"),
    app_commands.Choice(name="🏹 Paladin (RP)",  value="paladin"),
    app_commands.Choice(name="🌿 Druid (ED)",    value="druid"),
    app_commands.Choice(name="🔥 Sorcerer (MS)", value="sorcerer"),
    app_commands.Choice(name="🥊 Monk (EM)",     value="monk"),
])
async def perfil(
    interaction: discord.Interaction,
    char_name: str = None,
    vocacao: str = None,
    nivel: int = None,
):
    update_profile(
        interaction.user.id,
        **({"char_name": char_name} if char_name else {}),
        **({"vocation": vocacao} if vocacao else {}),
        **({"level": nivel} if nivel else {}),
    )
    profile = get_profile(interaction.user.id)
    lines = [
        f"👤 **Personagem:** {profile.get('char_name') or '*não definido*'}",
        f"🎭 **Vocação:** {profile.get('vocation') or '*não definida*'}",
        f"⚡ **Nível:** {profile.get('level') or '*não definido*'}",
        f"🤖 **IA preferida:** `{profile.get('preferred_ai', 'groq')}`",
    ]
    embed = make_embed(
        "✅ Perfil Salvo",
        "\n".join(lines) + "\n\nSuas próximas perguntas já vêm com contexto do seu personagem!",
        color=0x2ECC71
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="modelo", description="Escolhe a IA: Groq (gratuita) ou Claude (premium, se configurado)")
@app_commands.describe(ia="Escolha a IA para suas respostas")
@app_commands.choices(ia=[
    app_commands.Choice(name="🟢 Groq — Llama 3.1 (gratuito, rápido)", value="groq"),
    app_commands.Choice(name="🔵 Claude — Anthropic (premium, análise profunda)", value="claude"),
])
async def modelo(interaction: discord.Interaction, ia: str):
    if ia == "claude" and not CLAUDE_AVAILABLE:
        await interaction.response.send_message(
            "❌ Claude não está configurado. Peça ao admin para adicionar `ANTHROPIC_API_KEY` no `.env`.",
            ephemeral=True
        )
        return
    set_preferred_ai(interaction.user.id, ia)
    label = "Groq (Llama 3.1 — gratuito)" if ia == "groq" else "Claude (Anthropic)"
    await interaction.response.send_message(
        f"✅ IA alterada para **{label}**. Suas próximas respostas usarão este modelo.",
        ephemeral=True
    )


@tree.command(name="limpar", description="Limpa seu histórico de conversa")
async def limpar(interaction: discord.Interaction):
    clear_history(interaction.user.id)
    await interaction.response.send_message("🗑️ Histórico limpo! Posso começar do zero.", ephemeral=True)


@tree.command(name="status", description="Status técnico do bot")
async def status_cmd(interaction: discord.Interaction):
    from cache import character_cache, item_cache, creature_cache
    latency = round(bot.latency * 1000)
    desc = (
        f"🏓 **Latência Discord:** {latency}ms\n"
        f"\n**🤖 Modelos de IA:**\n{ai_status()}\n"
        f"\n**💾 Cache:**\n"
        f"Personagens: {character_cache.size()} entradas\n"
        f"Itens: {item_cache.size()} entradas\n"
        f"Criaturas: {creature_cache.size()} entradas\n"
        f"\n**📚 Knowledge Base:**\n{kb_status()}\n"
        f"\n**📊 Geral:**\n"
        f"Usuários com memória: {count_users()}\n"
        f"YouTube: {'✅ ativo' if YT_AVAILABLE else '⚪ não configurado'}\n"
        f"Servidores Discord: {len(bot.guilds)}\n"
    )
    embed = make_embed("⚙️ Status — Companion Tibia v3.0", desc, color=0x1ABC9C)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="wiki", description="Busca informações na wiki oficial do Rubinot")
@app_commands.describe(busca="O que buscar. Ex: Soulpit, Linked Tasks, Soul War Quest")
async def wiki_cmd(interaction: discord.Interaction, busca: str):
    await interaction.response.defer()
    # Tenta página direta primeiro, depois busca
    page = await run(get_wiki_page, busca)
    if page:
        desc = format_wiki_result(page)
        embed = make_embed(f"📖 Wiki — {page['title']}", desc, color=0x3498DB, url=page.get("url"))
        embed.set_footer(text=f"{FOOTER_TEXT} • Fonte: wiki.rubinot.com")
        await interaction.followup.send(embed=embed)
        return

    results = await run(search_wiki, busca)
    if results:
        desc = format_search_results(results)
        embed = make_embed(f"🔍 Wiki — Resultados para: {busca}", desc, color=0x3498DB)
        embed.set_footer(text=f"{FOOTER_TEXT} • Fonte: wiki.rubinot.com")
        await interaction.followup.send(embed=embed)
        return

    # Fallback: IA responde com KB
    answer, model = await run(ask_ai, interaction.user.id,
        f"Me dê informações sobre '{busca}' no Rubinot com base no que você sabe.")
    embed = make_embed(f"📖 {busca}", answer, model=model)
    await interaction.followup.send(embed=embed)


@tree.command(name="soulpit", description="Guia completo do Soulpit — quando entrar, estratégia e composições")
async def soulpit_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    page = await run(get_soulpit_info)
    if page and page.get("full_text"):
        desc = format_wiki_result(page)
        embed = make_embed("🌀 Soulpit — Guia Completo", desc, color=0x8B0000, url=page.get("url"))
        embed.set_footer(text=f"{FOOTER_TEXT} • Fonte: wiki.rubinot.com")
    else:
        answer, model = await run(ask_ai, interaction.user.id,
            "Guia completo do Soulpit no Rubinot: o que é, quando entrar, bônus de EXP, "
            "composição ideal, estratégia e dicas.")
        embed = make_embed("🌀 Soulpit — Guia Completo", answer, color=0x8B0000, model=model)
    await interaction.followup.send(embed=embed)


@tree.command(name="task", description="Info sobre Linked Tasks do Rubinot")
@app_commands.describe(criatura="Criatura/task específica (opcional). Deixe vazio para guia geral.")
async def task_cmd(interaction: discord.Interaction, criatura: str = ""):
    await interaction.response.defer()
    if criatura:
        answer, model = await run(ask_ai, interaction.user.id,
            f"Info sobre a Linked Task de '{criatura}' no Rubinot: requisito, objetivo, "
            f"recompensas, dica de estratégia.")
        embed = make_embed(f"📋 Task — {criatura}", answer, color=0x27AE60, model=model)
    else:
        page = await run(get_linked_tasks)
        if page and page.get("full_text"):
            desc = format_wiki_result(page)
            embed = make_embed("📋 Linked Tasks — Guia", desc, color=0x27AE60, url=page.get("url"))
            embed.set_footer(text=f"{FOOTER_TEXT} • Fonte: wiki.rubinot.com")
        else:
            answer, model = await run(ask_ai, interaction.user.id,
                "Guia das Linked Tasks do Rubinot: como funcionam, melhores por nível, recompensas.")
            embed = make_embed("📋 Linked Tasks — Guia", answer, color=0x27AE60, model=model)
    await interaction.followup.send(embed=embed)


@tree.command(name="eventos", description="Eventos ativos e próximos do Rubinot")
async def eventos_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    # Tenta buscar da wiki e da KB extra
    page = await run(get_wiki_page, "Events")
    if not page:
        page = await run(get_wiki_page, "Eventos")
    if page and len(page.get("full_text", "")) > 100:
        desc = format_wiki_result(page)
        embed = make_embed("🎉 Eventos — Rubinot", desc, color=0xF39C12, url=page.get("url"))
        embed.set_footer(text=f"{FOOTER_TEXT} • Fonte: wiki.rubinot.com")
    else:
        answer, model = await run(ask_ai, interaction.user.id,
            "Quais os eventos ativos, sazonais e regulares do servidor Rubinot? "
            "Inclua: Double EXP, Battle Pass, Castle System, eventos especiais e dicas para aproveitar cada um.")
        embed = make_embed("🎉 Eventos — Rubinot", answer, color=0xF39C12, model=model)
    await interaction.followup.send(embed=embed)


@tree.command(name="calc", description="Calculadora de EXP — quanto falta para o próximo nível")
@app_commands.describe(
    nivel_atual="Seu nível atual",
    nivel_alvo="Nível que quer alcançar",
    exp_hora="EXP por hora na sua hunt atual (ex: 1500000 para 1.5M)"
)
async def calc_cmd(interaction: discord.Interaction, nivel_atual: int, nivel_alvo: int, exp_hora: int = 0):
    await interaction.response.defer()

    if nivel_alvo <= nivel_atual:
        await interaction.followup.send("❌ O nível alvo precisa ser maior que o nível atual.", ephemeral=True)
        return

    # Fórmula de EXP do Tibia: EXP(n) = 50/3 * (n^3 - 6n^2 + 17n - 12)
    def exp_para_nivel(n: int) -> int:
        return max(0, int((50 / 3) * (n**3 - 6 * n**2 + 17 * n - 12)))

    exp_atual = exp_para_nivel(nivel_atual)
    exp_alvo  = exp_para_nivel(nivel_alvo)
    exp_falta = exp_alvo - exp_atual

    lines = [
        f"⚡ **Nível atual:** {nivel_atual}",
        f"🎯 **Nível alvo:** {nivel_alvo}",
        f"📊 **EXP necessária:** {exp_falta:,}",
    ]

    if exp_hora > 0:
        horas = exp_falta / exp_hora
        dias  = horas / 24
        horas_int = int(horas)
        minutos   = int((horas - horas_int) * 60)
        lines.append(f"⏱️ **Com {exp_hora:,} EXP/h:** {horas_int}h {minutos}min ({dias:.1f} dias)")

        # Ajuste com stamina (2h premium/dia = +50% EXP)
        horas_stamina = exp_falta / (exp_hora * 1.5)
        lines.append(f"💚 **Com stamina premium** (2h/dia 150%): {horas_stamina:.1f}h ({horas_stamina/24:.1f} dias)")

    if nivel_alvo - nivel_atual == 1:
        # Dica específica para 1 level
        pergunta = (
            f"Em 1 linha: qual a melhor hunt para subir do nível {nivel_atual} para {nivel_alvo} rápido no Rubinot?"
        )
        dica, model = await run(ask_ai, interaction.user.id, pergunta)
        lines.append(f"\n💡 **Dica:** {dica[:200]}")
    else:
        model = None

    embed = make_embed(
        f"🧮 Calc EXP — {nivel_atual} → {nivel_alvo}",
        "\n".join(lines),
        color=0x1ABC9C,
        model=model,
    )
    await interaction.followup.send(embed=embed)


@tree.command(name="castle", description="Info sobre o Castle System do Rubinot")
async def castle_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    page = await run(get_wiki_page, "Castle_System")
    if not page:
        page = await run(get_wiki_page, "Castle")
    if page and len(page.get("full_text", "")) > 100:
        desc = format_wiki_result(page)
        embed = make_embed("🏯 Castle System", desc, color=0xE74C3C, url=page.get("url"))
        embed.set_footer(text=f"{FOOTER_TEXT} • Fonte: wiki.rubinot.com")
    else:
        answer, model = await run(ask_ai, interaction.user.id,
            "Explique o Castle System do Rubinot: como funciona, horários, "
            "composição ideal, recompensas e estratégia para ganhar.")
        embed = make_embed("🏯 Castle System", answer, color=0xE74C3C, model=model)
    await interaction.followup.send(embed=embed)


@tree.command(name="recarregar_kb", description="[Admin] Recarrega a KB extra do GitHub")
async def recarregar_kb(interaction: discord.Interaction):
    content = await run(reload_kb)
    if content:
        await interaction.response.send_message(
            f"✅ KB extra recarregada: {len(content):,} chars", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "⚪ KB GitHub não configurada ou indisponível.", ephemeral=True
        )


# ── Comandos — Servidor ao vivo ───────────────────────────────────────────────

@tree.command(name="noticias", description="Últimas notícias e patches do servidor Rubinot")
async def noticias(interaction: discord.Interaction):
    await interaction.response.defer()
    news = await run(get_news, 5)
    if not news:
        # Fallback: IA comenta sobre updates recentes baseado na KB
        answer, model = await run(
            ask_ai, interaction.user.id,
            "Quais são as últimas mudanças e atualizações importantes do servidor Rubinot que você conhece?"
        )
        embed = make_embed("📰 Notícias — Rubinot", answer, color=0x3498DB, model=model)
    else:
        desc = format_news_embed(news)
        embed = make_embed("📰 Notícias — Rubinot Open PvP", desc, color=0x3498DB)
        embed.set_footer(text=f"{FOOTER_TEXT} • Fonte: rubinot.com.br")
    await interaction.followup.send(embed=embed)


@tree.command(name="online", description="Jogadores online agora no Rubinot")
async def online_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    data = await run(get_online_players)
    desc = format_online_embed(data)
    embed = make_embed("🟢 Online — Rubinot Open PvP", desc, color=0x2ECC71)
    embed.set_footer(text=f"{FOOTER_TEXT} • Atualizado a cada 60s")
    await interaction.followup.send(embed=embed)


@tree.command(name="guilds", description="Lista as guilds ativas do servidor Rubinot")
async def guilds_list_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    guilds = await run(get_guilds_list)
    if not guilds:
        embed = make_embed(
            "🏰 Guilds — Rubinot",
            "Não foi possível carregar a lista de guilds.\n"
            "🔗 [Ver no site](<https://rubinot.com.br/guilds>)",
            color=0xF39C12,
        )
        await interaction.followup.send(embed=embed)
        return
    lines = [f"**Total: {len(guilds)} guilds**\n"]
    for g in guilds[:20]:
        members = f" ({g['members']} membros)" if g.get("members") else ""
        desc_short = f" — {g['description'][:60]}..." if g.get("description") else ""
        lines.append(f"🏰 **{g['name']}**{members}{desc_short}")
    embed = make_embed("🏰 Guilds Ativas — Rubinot", "\n".join(lines), color=0xF39C12)
    embed.set_footer(text=f"{FOOTER_TEXT} • Use /guild [nome] para detalhes")
    await interaction.followup.send(embed=embed)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logger.error("❌ DISCORD_TOKEN não encontrado. Configure o arquivo .env")
        exit(1)
    if not os.getenv("GROQ_API_KEY"):
        logger.error("❌ GROQ_API_KEY não encontrada. Configure o arquivo .env")
        exit(1)

    start_keep_alive()
    logger.info("🚀 Iniciando Companion Tibia v3.0...")
    bot.run(DISCORD_TOKEN, log_handler=None)
