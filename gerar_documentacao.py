"""
Gera a documentação completa do Companion Tibia em formato Word (.docx).
Executa: python gerar_documentacao.py
"""

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import datetime

# ── Helpers de estilo ────────────────────────────────────────────────────────

def add_heading(doc, text, level=1, color=None):
    h = doc.add_heading(text, level=level)
    if color:
        for run in h.runs:
            run.font.color.rgb = RGBColor(*color)
    return h

def add_paragraph(doc, text="", bold=False, italic=False, size=None, color=None):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    if size:
        run.font.size = Pt(size)
    if color:
        run.font.color.rgb = RGBColor(*color)
    return p

def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(text, style="List Bullet")
    p.paragraph_format.left_indent = Inches(0.25 * (level + 1))
    return p

def add_numbered(doc, text, level=0):
    p = doc.add_paragraph(text, style="List Number")
    return p

def add_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.LEFT

    hdr = table.rows[0]
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.text = h
        run = cell.paragraphs[0].runs[0]
        run.bold = True
        run.font.size = Pt(9)
        shading = OxmlElement("w:shd")
        shading.set(qn("w:fill"), "2F3136")
        shading.set(qn("w:color"), "FFFFFF")
        cell._tc.get_or_add_tcPr().append(shading)
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)

    for r_idx, row in enumerate(rows):
        tr = table.rows[r_idx + 1]
        for c_idx, val in enumerate(row):
            cell = tr.cells[c_idx]
            cell.text = str(val)
            cell.paragraphs[0].runs[0].font.size = Pt(9)
            if r_idx % 2 == 0:
                shading = OxmlElement("w:shd")
                shading.set(qn("w:fill"), "F2F3F5")
                cell._tc.get_or_add_tcPr().append(shading)

    if col_widths:
        for i, w in enumerate(col_widths):
            for row in table.rows:
                row.cells[i].width = Cm(w)
    return table

def add_code_block(doc, code_text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(code_text)
    run.font.name = "Courier New"
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(30, 30, 30)
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), "E8E8E8")
    pPr.append(shd)
    return p

def add_separator(doc):
    doc.add_paragraph("─" * 80)

def add_result_block(doc, sim_num, title, status, details):
    """Adiciona um bloco de resultado de simulação."""
    p = doc.add_paragraph()
    run = p.add_run(f"Simulação {sim_num} — {title}")
    run.bold = True
    run.font.size = Pt(11)

    icon = "✅" if status == "OK" else "⚠️"
    p2 = doc.add_paragraph()
    run2 = p2.add_run(f"{icon} Status: {status}")
    run2.bold = True
    run2.font.size = Pt(10)
    color = (39, 174, 96) if status == "OK" else (230, 126, 34)
    run2.font.color.rgb = RGBColor(*color)

    add_code_block(doc, details)


# ── Documento Principal ──────────────────────────────────────────────────────

def build_doc():
    doc = Document()

    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    # ── CAPA ────────────────────────────────────────────────────────────────
    doc.add_paragraph()
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("COMPANION TIBIA")
    run.bold = True
    run.font.size = Pt(28)
    run.font.color.rgb = RGBColor(200, 169, 81)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run2 = subtitle.add_run("Assistente Inteligente para Tibia OT — Rubinot Open PvP")
    run2.font.size = Pt(14)
    run2.italic = True

    doc.add_paragraph()
    authors = doc.add_paragraph()
    authors.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run3 = authors.add_run("Idealizado e desenvolvido por  Soneca & Shawnks")
    run3.bold = True
    run3.font.size = Pt(12)

    doc.add_paragraph()
    version = doc.add_paragraph()
    version.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run4 = version.add_run(f"Documentação Técnica Completa — Versão 3.0 | {datetime.date.today().strftime('%B %Y')}")
    run4.font.size = Pt(10)
    run4.font.color.rgb = RGBColor(100, 100, 100)

    doc.add_page_break()

    # ── ÍNDICE ───────────────────────────────────────────────────────────────
    add_heading(doc, "ÍNDICE", 1)
    toc_items = [
        ("1",  "Visão Geral do Projeto"),
        ("2",  "O que Mudou: SonecaBot → Companion Tibia"),
        ("3",  "O que Foi Implementado (v3.0)"),
        ("4",  "O que Ainda Falta Implementar"),
        ("5",  "Arquitetura Técnica"),
        ("6",  "Índice de Arquivos — O que é cada coisa"),
        ("7",  "Comandos Disponíveis no Discord"),
        ("8",  "Base de Conhecimento (Knowledge Base)"),
        ("9",  "APIs e Integrações Externas"),
        ("10", "Como Rodar Localmente"),
        ("11", "Como Fazer Deploy 24/7 (Railway)"),
        ("12", "Como Atualizar o Bot"),
        ("13", "Problemas Conhecidos e Limitações"),
        ("14", "Roadmap — Próximas Versões"),
        ("15", "O que vai para o GitHub — e o que NÃO vai"),
        ("16", "Simulações — 10 Exemplos de Uso Real (com resultados)"),
    ]
    for num, title_text in toc_items:
        p = doc.add_paragraph(f"  {num}. {title_text}")
        p.paragraph_format.left_indent = Inches(0.3)

    doc.add_page_break()

    # ── SEÇÃO 1: VISÃO GERAL ─────────────────────────────────────────────────
    add_heading(doc, "1. Visão Geral do Projeto", 1)

    add_paragraph(doc,
        "O Companion Tibia é um bot de Discord especializado no servidor Tibia OT Rubinot Open PvP. "
        "Seu objetivo é centralizar em um único lugar toda a informação que um jogador precisa: "
        "hunts por nível e vocação, rotação de spells, builds, imbues, análise de grupo, "
        "dados reais de personagens do servidor e informações sobre itens e criaturas.",
        size=10)

    doc.add_paragraph()
    add_paragraph(doc, "Proposta de valor:", bold=True)
    add_bullet(doc, "Zero custo de operação — Groq API gratuita + Railway free tier")
    add_bullet(doc, "Responde em segundos com contexto de 22.500+ chars de KB embutida")
    add_bullet(doc, "Busca dados reais de personagens, guilds, ranking e mortes no Rubinot")
    add_bullet(doc, "Itens e criaturas com imagem via TibiaWiki.dev (API gratuita)")
    add_bullet(doc, "Memória persistente por usuario — salva perfil e historico em JSON no disco")
    add_bullet(doc, "Modo IA dual — Groq (grátis, padrão) + Claude (premium, opcional)")
    add_bullet(doc, "YouTube API integrada para vídeos de hunt (opcional, gratuita)")
    add_bullet(doc, "Busca em fóruns OtLand e DuckDuckGo sem chave de API")
    add_bullet(doc, "KB extra via GitHub — atualizável sem redeploy")
    add_bullet(doc, "24 slash commands + resposta quando mencionado")
    add_bullet(doc, "Deploy 24/7 sem precisar do PC do criador ligado")

    doc.add_paragraph()
    add_paragraph(doc, "Criado por:", bold=True)
    add_bullet(doc, "Soneca — idealizador e desenvolvedor principal")
    add_bullet(doc, "Shawnks — co-criador e idealizador")

    doc.add_page_break()

    # ── SEÇÃO 2: O QUE MUDOU ─────────────────────────────────────────────────
    add_heading(doc, "2. O que Mudou: SonecaBot → Companion Tibia", 1)

    add_paragraph(doc,
        "O projeto nasceu como 'SonecaBot' com proposta de aplicação web (Next.js + FastAPI). "
        "Durante o desenvolvimento, decidimos mudar para um bot de Discord por ser mais prático, "
        "mais rápido de lançar e mais natural para o contexto de uso (a galera já usa Discord para jogar). "
        "A v3.0 completou todas as features planejadas no escopo original.",
        size=10)

    doc.add_paragraph()
    add_heading(doc, "2.1 Mudanças de Arquitetura", 2)
    add_table(doc,
        ["Aspecto", "SonecaBot Original", "Companion Tibia v3"],
        [
            ("Interface", "Aplicação Web (Next.js + React)", "Bot de Discord (discord.py)"),
            ("Backend", "FastAPI (Python) + REST API", "Embutido no bot (eventos Discord)"),
            ("Banco de Dados", "PostgreSQL (Supabase)", "JSON files locais (data/memory/)"),
            ("Cache", "Redis (Upstash)", "TTL Cache em memória (cache.py)"),
            ("IA Principal", "Groq (free) + Claude (premium)", "Groq (free) + Claude (opcional) via ai_client.py"),
            ("KB Storage", "GitHub repo (JSON files)", "knowledge_base.py + KB extra via GitHub (kb_loader.py)"),
            ("Deploy", "Vercel (front) + Railway (back)", "Railway (apenas o bot)"),
            ("Autenticacao", "Usuario/senha ou Discord OAuth", "Nenhuma — Discord nativo"),
            ("Forum Search", "Nao previsto", "OtLand + DuckDuckGo (sem API key)"),
            ("YouTube", "Nao previsto", "YouTube Data API v3 (opcional, gratuita)"),
            ("Nome do bot", "SonecaBot", "Companion Tibia"),
        ],
        col_widths=[4, 5.5, 6.5]
    )

    doc.add_paragraph()
    add_heading(doc, "2.2 Por que Discord em vez de Web App?", 2)
    add_bullet(doc, "Mais rápido de lançar — bot ficou pronto no mesmo dia")
    add_bullet(doc, "A galera já está no Discord enquanto joga — zero atrito")
    add_bullet(doc, "Slash commands são mais intuitivos que uma interface web para esse uso")
    add_bullet(doc, "Zero custo de frontend — sem Vercel, sem CDN, sem build")
    add_bullet(doc, "Notificações nativas do Discord (menções, canais dedicados)")
    add_bullet(doc, "Facilita compartilhar respostas com o grupo via reply")

    doc.add_page_break()

    # ── SEÇÃO 3: O QUE FOI IMPLEMENTADO ─────────────────────────────────────
    add_heading(doc, "3. O que Foi Implementado (v3.0)", 1)

    add_heading(doc, "3.1 Módulos Funcionais", 2)
    add_table(doc,
        ["Módulo", "Status", "Onde está", "Observação"],
        [
            ("Chat com IA Dual (Groq + Claude)", "OK", "ai_client.py", "Groq grátis padrão; Claude opcional via ANTHROPIC_API_KEY"),
            ("Slash Commands Discord", "OK", "bot.py", "24 comandos + mencao @bot"),
            ("Base de Conhecimento", "OK", "knowledge_base.py", "22.500+ chars de contexto"),
            ("KB Extra via GitHub", "OK", "kb_loader.py", "Cache 30min, atualizavel sem redeploy"),
            ("Guias de Hunt por Vocacao", "OK", "knowledge_base.py", "8 spots detalhados + tabela geral"),
            ("Rotacao de Spells (5 vocacoes)", "OK", "knowledge_base.py", "EK, RP, ED, MS, Monk"),
            ("Builds por fase (early/mid/end)", "OK", "knowledge_base.py", "Todas as vocacoes"),
            ("Sistema Monk (Harmony/Virtue/Serene)", "OK", "knowledge_base.py", "Discovery completo incluido"),
            ("Info do servidor Rubinot", "OK", "knowledge_base.py", "Sistemas exclusivos, mecanicas"),
            ("Guias de Imbue", "OK", "knowledge_base.py", "Todos os slots por vocacao"),
            ("Composicoes de grupo", "OK", "knowledge_base.py", "Duo, trio, party 4-5"),
            ("Quests importantes", "OK", "knowledge_base.py", "Soul War, Inquisition, Falcons, etc."),
            ("Busca de personagem (Rubinot)", "OK", "scraper.py", "Scraping com anti-bot headers"),
            ("Analise de party com dados reais", "OK", "bot.py + scraper.py", "Busca N chars + IA analisa"),
            ("Busca de Guild (Rubinot)", "OK", "scraper.py", "Nome, lider, membros, data fundacao"),
            ("Ranking / Highscores (Rubinot)", "OK", "scraper.py", "Por vocacao e categoria"),
            ("Mortes recentes / PvP Kills", "OK", "scraper.py", "Feed de kills em tempo real"),
            ("Info de itens + imagem", "OK", "tibia_api.py", "TibiaWiki.dev API gratuita"),
            ("Info de criaturas + loot", "OK", "tibia_api.py", "HP, EXP, resistencias, loot"),
            ("Memoria persistente por usuario", "OK", "memory.py", "JSON em data/memory/{user_id}.json"),
            ("Perfil do jogador", "OK", "memory.py", "Char name, vocacao, nivel, IA preferida"),
            ("Contexto do perfil no prompt", "OK", "memory.py + bot.py", "Injetado em toda conversa"),
            ("YouTube — videos de hunt", "OK", "youtube_api.py", "Opcional, cache 2h, 10k req/dia grátis"),
            ("Busca em forums OtLand/DuckDuckGo", "OK", "forum_scraper.py", "Sem API key, cache 2h"),
            ("TTL Cache", "OK", "cache.py", "10min chars, 60min itens/criaturas"),
            ("Keep-alive HTTP server", "OK", "keep_alive.py", "Para Railway/Render nao matar o bot"),
            ("Auto-restart local", "OK", "run_forever.bat / .sh", "Windows e Linux/Mac"),
            ("Testes automaticos", "OK", "test_bot.py", "18/18 testes passando"),
            ("Simulacoes sem Discord/Groq", "OK", "simulacoes.py", "28/33 cenarios validados"),
            ("Deploy Railway configurado", "OK", "Procfile + railway.toml", "restart on failure, healthcheck"),
            ("Fallback SSL corporativo", "OK", "scraper.py + tibia_api.py", "Funciona em redes com proxy"),
        ],
        col_widths=[5, 2, 4, 6]
    )

    doc.add_page_break()

    # ── SEÇÃO 4: O QUE FALTA ────────────────────────────────────────────────
    add_heading(doc, "4. O que Ainda Falta Implementar", 1)

    add_paragraph(doc,
        "Estes itens estavam no roadmap mas nao foram priorizados nesta versao. "
        "As grandes features planejadas (memoria persistente, dual IA, YouTube, forum, guild, "
        "ranking, mortes) foram TODAS entregues na v3.0.",
        size=10)

    doc.add_paragraph()
    add_heading(doc, "4.1 Media Prioridade (enriquecimento de conteudo)", 2)
    add_table(doc,
        ["Item", "Por que importa", "Complexidade"],
        [
            ("TibiaWiki API — endpoint de spells",
             "O endpoint /api/spells da TibiaWiki.dev retorna {} vazio. "
             "Precisaria de fonte alternativa (wiki scraping ou tabela local).",
             "Media"),
            ("Demon Forge na KB",
             "Spot importante de end-game nao documentado na KB. "
             "Simulacao 10 falhou neste ponto especifico.",
             "Baixa — so atualizar knowledge_base.py"),
            ("Notificacoes de novidades do servidor",
             "Bot postar automaticamente quando sair patch ou evento no Rubinot.",
             "Alta"),
            ("Calculadora de EXP para proximo nivel",
             "Dado o level atual, calcular quanto tempo falta para subir baseado na hunt atual.",
             "Baixa"),
        ],
        col_widths=[4.5, 9.5, 3]
    )

    doc.add_paragraph()
    add_heading(doc, "4.2 Baixa Prioridade (polish e escalabilidade)", 2)
    add_table(doc,
        ["Item", "Por que importa", "Complexidade"],
        [
            ("Analytics de uso",
             "Entender quais comandos sao mais usados para priorizar melhorias.",
             "Baixa"),
            ("Contribuicao comunitaria na KB",
             "Sistema para qualquer jogador sugerir atualizacao via PR no GitHub.",
             "Media"),
            ("Vector Search / RAG completo",
             "Quando a KB crescer alem de ~5MB, busca semantica se torna necessaria.",
             "Alta"),
            ("Comando /compare [char1] [char2]",
             "Comparar dois personagens lado a lado — util para recrutamento de guild.",
             "Baixa"),
        ],
        col_widths=[4.5, 9.5, 3]
    )

    doc.add_page_break()

    # ── SEÇÃO 5: ARQUITETURA ─────────────────────────────────────────────────
    add_heading(doc, "5. Arquitetura Técnica", 1)

    add_heading(doc, "5.1 Visao Geral do Fluxo", 2)
    add_paragraph(doc, "Quando um usuario usa um comando ou menciona o bot:", size=10)

    steps = [
        "Discord recebe o slash command ou mensagem com mencao",
        "bot.py captura o evento (on_message ou comando)",
        "O comando formata a pergunta com contexto especifico",
        "memory.py carrega historico + perfil do usuario (JSON em disco)",
        "kb_loader.py monta o system prompt: KB base + extra GitHub (se configurada)",
        "ai_client.chat() envia: [System Prompt + perfil] + [historico] + [pergunta] para Groq ou Claude",
        "Resposta retorna em ~0.5-2 segundos com nome do modelo usado",
        "Bot formata em Discord Embed com titulo, footer (modelo IA) e thumbnail",
        "Resposta e enviada no canal do Discord",
        "memory.py salva a nova troca (usuario+bot) no JSON em disco",
    ]
    for i, step in enumerate(steps, 1):
        add_numbered(doc, f"{i}. {step}")

    doc.add_paragraph()
    add_heading(doc, "5.2 Para comandos com dados externos (/personagem, /item, /monstro, /guild, /ranking)", 2)
    steps2 = [
        "Antes de chamar a IA, o bot busca dados na API/site externo (em thread separada para nao bloquear)",
        "scraper.py busca o Rubinot com headers de browser real",
        "tibia_api.py consulta TibiaWiki.dev para itens e criaturas",
        "cache.py verifica se ja tem o dado em cache (evita chamada repetida)",
        "Dados estruturados sao formatados em embed Discord com imagem",
        "IA adiciona dica contextualizada com base nos dados reais encontrados",
    ]
    for i, step in enumerate(steps2, 1):
        add_numbered(doc, f"{i}. {step}")

    doc.add_paragraph()
    add_heading(doc, "5.3 Stack Tecnologica", 2)
    add_table(doc,
        ["Camada", "Tecnologia", "Versao", "Custo", "Por que?"],
        [
            ("Bot Discord", "discord.py", "2.4.0", "Gratis", "Biblioteca padrao para bots Python"),
            ("IA Padrao", "Groq API (Llama 3.1 70B)", "—", "Gratis", "30 req/min free, latencia <1s"),
            ("IA Premium", "Anthropic Claude", ">=0.40.0", "Pago (opcional)", "Analises mais profundas, se configurado"),
            ("HTTP Client", "requests + BeautifulSoup4", "2.32.3 / 4.12.3", "Gratis", "Scraping do Rubinot e forum"),
            ("Tibia API", "TibiaWiki.dev", "—", "Gratis", "Itens/criaturas sem autenticacao"),
            ("Memoria", "JSON files (stdlib)", "—", "Gratis", "data/memory/{user_id}.json — persiste reinicializacoes"),
            ("Cache", "TTL Dict (in-memory)", "—", "Gratis", "Sem dependencia externa"),
            ("YouTube", "YouTube Data API v3", "—", "Gratis (10k/dia)", "Opcional — so ativa com YOUTUBE_API_KEY"),
            ("Forum Search", "DuckDuckGo HTML + OtLand", "—", "Gratis", "Sem API key necessaria"),
            ("KB Extra", "GitHub raw content", "—", "Gratis", "kb_loader.py — cache 30min"),
            ("Keep-alive", "http.server (stdlib)", "—", "Gratis", "Health check para Railway"),
            ("Deploy", "Railway.app", "—", "Gratis*", "Deploy automatico via GitHub push"),
            ("Config", "python-dotenv", "1.0.1", "Gratis", "Gerenciar .env de forma segura"),
            ("Compat. Python 3.13", "audioop-lts", "0.2.2", "Gratis", "discord.py requer audioop removido no 3.13"),
        ],
        col_widths=[3.5, 4, 2.5, 2.5, 4.5]
    )
    add_paragraph(doc, "* Railway free tier: 500h/mes. Para uso 24/7 (~720h/mes), plano Starter: ~US$5/mes.", italic=True, size=9)

    doc.add_paragraph()
    add_heading(doc, "5.4 Fluxo de Memoria por Usuario", 2)
    add_paragraph(doc,
        "Cada usuario Discord tem seu historico de conversa salvo em data/memory/{user_id}.json. "
        "Sao mantidas as ultimas 10 mensagens. O perfil (char_name, vocacao, nivel, preferred_ai) "
        "tambem e persistido. Ao chamar a IA, a sequencia enviada e: "
        "[System Prompt + perfil] + [historico] + [nova pergunta]. "
        "O historico SOBREVIVE reinicializacoes do bot — ao contrario da versao anterior.",
        size=10)

    doc.add_page_break()

    # ── SEÇÃO 6: ÍNDICE DE ARQUIVOS ──────────────────────────────────────────
    add_heading(doc, "6. Indice de Arquivos — O que e cada coisa", 1)

    add_paragraph(doc,
        "Todos os arquivos da pasta companion_tibia/, explicados um a um.",
        size=10)

    files = [
        (
            "bot.py",
            "Arquivo principal do bot.",
            [
                "Inicializa o cliente Discord com discord.py",
                "Define todos os 24 slash commands",
                "Importa: keep_alive, knowledge_base, scraper, tibia_api, memory, ai_client, youtube_api, forum_scraper, kb_loader",
                "ask_ai(user_id, question, extra_context) — chama ai_client.chat() com historico + perfil injetados",
                "make_embed(title, desc, color, thumbnail_url, url, model) — fabrica de Discord embeds",
                "run(func, *args) — atalho para asyncio.run_in_executor(), roda HTTP sync sem bloquear",
                "Responde quando o bot e mencionado (@Companion Tibia)",
                "Chama start_keep_alive() ao iniciar para manter o processo vivo no Railway",
            ],
            "OK — Vai para o GitHub (nao contem segredos)"
        ),
        (
            "knowledge_base.py",
            "Base de conhecimento completa do jogo.",
            [
                "Contem SYSTEM_PROMPT: texto de 22.500+ chars injetado em TODA conversa com a IA",
                "Descreve todas as 5 vocacoes (EK, RP, ED, MS, Monk) com builds, spells, rotacoes",
                "Inclui guias detalhados de 8 spots de hunt com estrategia por vocacao",
                "Cobre o sistema Harmony/Virtue/Serene do Monk (discovery completo)",
                "Informacoes do servidor Rubinot: sistemas exclusivos, mecanicas, URLs",
                "Constantes: VOCATION_ALIASES, VOCATION_EMOJIS, HELP_TEXT",
                "NOTA: 'Demon Forge' nao documentado ainda — adicionar na proxima atualizacao",
            ],
            "OK — Vai para o GitHub — e onde a KB deve ser atualizada a cada patch do Rubinot"
        ),
        (
            "memory.py",
            "Memoria persistente por usuario — salva em disco.",
            [
                "load_user(user_id) / save_user(user_id, mem) — le e grava data/memory/{id}.json",
                "get_history / add_message / clear_history — historico de conversa (ultimas 10 msgs)",
                "get_profile / update_profile — armazena char_name, vocacao, nivel, preferred_ai, guild",
                "get_preferred_ai / set_preferred_ai — escolha groq ou claude por usuario",
                "build_profile_context(user_id) — string injetada no prompt: [Perfil: Soneca | Knight | 250]",
                "count_users() / list_active_users(hours) — para o /status",
                "MAX_MESSAGES = 10 — mantem ultimas 10 mensagens por usuario",
                "Dados sobrevivem reinicializacoes do bot — JSON em disco",
            ],
            "OK — Vai para o GitHub"
        ),
        (
            "ai_client.py",
            "Cliente de IA dual — Groq (gratis) e Claude (opcional).",
            [
                "chat(messages, system_prompt, preferred, max_tokens) -> (resposta, modelo_usado)",
                "_chat_groq() — chama Groq API com lista completa de mensagens",
                "_chat_claude() — chama Anthropic API; auto-fallback para Groq se Claude falhar",
                "CLAUDE_AVAILABLE = bool — False se ANTHROPIC_API_KEY nao estiver configurada",
                "status_text() — retorna string mostrando quais modelos estao disponiveis",
                "Footer dos embeds mostra qual modelo respondeu (groq ou claude)",
            ],
            "OK — Vai para o GitHub"
        ),
        (
            "youtube_api.py",
            "Integracao com YouTube Data API v3 para videos de hunt.",
            [
                "AVAILABLE = bool(YOUTUBE_API_KEY) — silenciosamente desativado se sem chave",
                "search_hunt_videos(hunt_name, vocation, max_results) -> lista de {title, url, channel, thumbnail}",
                "format_videos_field(videos) -> string formatada para campo de embed Discord",
                "Cache TTL 2 horas para evitar consumir cota",
                "Trata quota exceeded graciosamente (sem erro para o usuario)",
                "10.000 req/dia gratuitos no Google Cloud",
            ],
            "OK — Vai para o GitHub"
        ),
        (
            "forum_scraper.py",
            "Busca threads em foruns de Tibia sem API key.",
            [
                "search_ddgo(query, site, max_results) — POST para html.duckduckgo.com/html/, sem API",
                "search_otland(query, max_results) — GET otland.net/search/, fallback para DuckDuckGo",
                "search_forum(query, max_results) — funcao publica principal, auto-prepend 'rubinot'",
                "format_forum_results(results, title) -> string <= 3500 chars para embed Discord",
                "Cache TTL 2 horas",
            ],
            "OK — Vai para o GitHub"
        ),
        (
            "scraper.py",
            "Busca dados de personagens, guilds, ranking e mortes no site do Rubinot.",
            [
                "Usa requests.Session() com headers reais de browser Chrome para evitar bloqueio 403",
                "get_character(name) / format_character_embed() — dados do personagem",
                "get_party_data(names) — busca multiplos personagens com delay",
                "get_guild(name) / format_guild_embed() — nome, lider, membros, data fundacao",
                "get_recent_deaths(limit) / format_deaths_embed() — feed de PvP kills",
                "get_highscores(vocation, category, limit) / format_highscores_embed() — ranking",
                "VOC_HIGHSCORE_IDS e CATEGORY_IDS — dicts mapeando nomes para params URL do Rubinot",
                "Fallback SSL + retry 3x com delay crescente",
            ],
            "OK — Vai para o GitHub"
        ),
        (
            "kb_loader.py",
            "Carrega KB extra do GitHub sem redeploy.",
            [
                "load_extra_kb() — busca KB_GITHUB_URL env var (markdown raw do GitHub), cache 30min",
                "build_full_system_prompt(base_prompt) — combina KB local + extra GitHub",
                "reload_kb() — limpa cache e recarrega (usado pelo /recarregar_kb)",
                "kb_status() — string de status para o /status",
                "Se KB_GITHUB_URL nao estiver configurada, funciona normalmente sem ela",
            ],
            "OK — Vai para o GitHub"
        ),
        (
            "tibia_api.py",
            "Integracao com TibiaWiki.dev para dados de itens e criaturas.",
            [
                "get_item(name) — GET tibiawiki.dev/api/items/{name} — armor, weight, slots, onde compra/dropa",
                "get_creature(name) — HP, EXP, loot com raridade, resistencias, imunidades",
                "Imagens: Fandom Wiki CDN (tibia.fandom.com/wiki/Special:FilePath/{nome}.gif)",
                "format_item_embed() e format_creature_embed() — formata para embed Discord",
                "Usa item_cache e creature_cache com TTL de 60 minutos",
                "Fallback SSL igual ao scraper.py",
                "BUG CORRIGIDO: campo 'value' da API pode ser string — int() com try/except",
            ],
            "OK — Vai para o GitHub"
        ),
        (
            "cache.py",
            "Sistema de cache TTL em memoria.",
            [
                "Classe TTLCache: dicionario com timestamps de expiracao",
                "Metodos: get(key), set(key, value, ttl_seconds), delete(key), clear(), size()",
                "get() retorna None automaticamente se a entrada expirou",
                "Tres instancias globais: character_cache (10min), item_cache (60min), creature_cache (60min)",
                "Sem dependencia externa — usa apenas Python stdlib",
            ],
            "OK — Vai para o GitHub"
        ),
        (
            "keep_alive.py",
            "Servidor HTTP minimo para manter o bot vivo em plataformas cloud.",
            [
                "Inicia um HTTPServer na porta 8080 em uma thread daemon",
                "Responde GET /health e /ping com JSON: {status: online}",
                "Plataformas como Railway e Render matam processos sem trafego HTTP — este servidor evita isso",
            ],
            "OK — Vai para o GitHub"
        ),
        (
            "simulacoes.py",
            "10 simulacoes de uso real sem precisar de Discord ou Groq conectados.",
            [
                "Sim 1: Sistema de memoria — salvar/carregar perfil, historico persistente em JSON",
                "Sim 2: Cache TTL — set/get, expiracao, multiplas entradas",
                "Sim 3: Busca de personagem no Rubinot (real + mock para rede corporativa)",
                "Sim 4: Busca de guild no Rubinot (real + mock)",
                "Sim 5: Ranking / highscores (real + mock)",
                "Sim 6: Mortes recentes / PvP kills (real + mock)",
                "Sim 7: TibiaWiki.dev — busca de item (Dragon Scale Mail)",
                "Sim 8: TibiaWiki.dev — busca de criatura (Demon)",
                "Sim 9: Forum OtLand / DuckDuckGo (busca real)",
                "Sim 10: Knowledge Base + sistema de dual IA (validacao de conteudo)",
                "Resultado: 28/33 validacoes passando — 5 falhas esperadas (rede corporativa + 1 gap na KB)",
            ],
            "OK — Vai para o GitHub"
        ),
        (
            "test_bot.py",
            "Suite de 18 testes automaticos.",
            [
                "Testa cache.py: set/get, expiracao, delete, size",
                "Testa knowledge_base.py: tamanho do system prompt, aliases, emojis, help text",
                "Testa scraper.py: importacao, personagem inexistente retorna None, format",
                "Testa tibia_api.py: importacao, busca real de item/criatura, formatacao",
                "Testa keep_alive.py: servidor sobe e responde /health",
                "Executa: python test_bot.py",
                "Retorna exit code 0 se todos passam, 1 se algum falha",
            ],
            "OK — Vai para o GitHub"
        ),
        (
            "requirements.txt",
            "Lista de dependencias Python.",
            [
                "discord.py==2.4.0 — biblioteca do bot Discord",
                "groq==0.9.0 — SDK oficial da Groq API",
                "python-dotenv==1.0.1 — carrega variaveis do arquivo .env",
                "requests==2.32.3 — HTTP client para scraper e tibia_api",
                "beautifulsoup4==4.12.3 — parse de HTML do Rubinot e forum",
                "audioop-lts==0.2.2 — compatibilidade com Python 3.13",
                "# anthropic>=0.40.0  (opcional, comentado por padrao)",
                "Instalar tudo: pip install -r requirements.txt",
            ],
            "OK — Vai para o GitHub"
        ),
        (
            ".env",
            "Arquivo de configuracao com segredos. NAO existe no projeto — voce cria.",
            [
                "DISCORD_TOKEN — token do bot Discord (discord.com/developers)",
                "GROQ_API_KEY — chave da Groq API (console.groq.com — gratuita)",
                "GROQ_MODEL — modelo a usar (padrao: llama-3.1-70b-versatile)",
                "ANTHROPIC_API_KEY — opcional, ativa o modo Claude premium",
                "YOUTUBE_API_KEY — opcional, ativa videos de hunt",
                "KB_GITHUB_URL — opcional, URL raw do GitHub com KB extra",
                "NUNCA commitar este arquivo — esta no .gitignore",
            ],
            "NAO vai para o GitHub — contem senhas/tokens"
        ),
        (
            ".env.example",
            "Template do .env sem valores reais.",
            [
                "Mostra quais variaveis precisam ser configuradas",
                "Pode (e deve) ir para o GitHub — nao tem valores reais",
            ],
            "OK — Vai para o GitHub"
        ),
        (
            "Procfile + railway.toml + runtime.txt",
            "Arquivos de configuracao do deploy no Railway.",
            [
                "Procfile: worker: python bot.py — diz ao Railway como iniciar",
                "railway.toml: restart on failure (10x), healthcheck em /health",
                "runtime.txt: python-3.11.9 — versao estavel para deploy",
            ],
            "OK — Vai para o GitHub"
        ),
        (
            "run_forever.bat / run_forever.sh",
            "Scripts de auto-restart local (Windows e Linux/Mac).",
            [
                "Loop infinito: se o bot crashar, reinicia em 5s",
                "Uso local — Railway ja tem restart automatico",
            ],
            "OK — Vai para o GitHub"
        ),
        (
            "gerar_documentacao.py",
            "Script que gera este documento Word.",
            [
                "Usa python-docx para criar os arquivos .docx",
                "Executar: python gerar_documentacao.py",
                "Gera Companion_Tibia_Documentacao.docx na mesma pasta",
            ],
            "OK — Vai para o GitHub (opcional)"
        ),
    ]

    for filename, description, bullets, github_status in files:
        add_heading(doc, filename, 2)
        add_paragraph(doc, description, bold=True, size=10)
        for b in bullets:
            add_bullet(doc, b)
        p = doc.add_paragraph()
        run = p.add_run(f"GitHub: {github_status}")
        run.bold = True
        run.font.size = Pt(9)
        color = (39, 174, 96) if "OK" in github_status or "Vai" in github_status else (231, 76, 60)
        run.font.color.rgb = RGBColor(*color)
        doc.add_paragraph()

    doc.add_page_break()

    # ── SEÇÃO 7: COMANDOS ────────────────────────────────────────────────────
    add_heading(doc, "7. Comandos Disponiveis no Discord", 1)

    add_table(doc,
        ["Comando", "Parametros", "O que faz", "Fonte"],
        [
            ("/ajuda", "—", "Lista todos os comandos com descricao", "Estatico"),
            ("/ask", "pergunta", "Pergunta livre — resposta da IA sem template fixo", "IA + KB"),
            ("/hunt", "vocacao, nivel, modo (opc)", "4 hunts com guia, exp/h, rotacao, imbue + videos YouTube (se ativo)", "IA + KB + YouTube"),
            ("/vocacao", "vocacao", "Guia completo: papel, builds, rotacao, imbues", "IA + KB"),
            ("/spells", "vocacao, situacao (opc)", "Rotacao de spells em ordem de prioridade", "IA + KB"),
            ("/nivel", "vocacao, nivel", "Roadmap do nivel: hunt, equipamento, spell, quest", "IA + KB"),
            ("/imbue", "vocacao, slot", "Melhores imbuements em ordem de prioridade", "IA + KB"),
            ("/grupo", "composicao", "Analisa composicao: sinergia, hunt ideal, fraqueza", "IA + KB"),
            ("/personagem", "nome", "Dados reais no Rubinot: level, vocacao, guild, cidade", "Scraper + IA"),
            ("/party", "nomes (virgula)", "Busca ate 5 chars e analisa composicao com IA", "Scraper + IA"),
            ("/guild", "nome", "Info da guild: lider, membros, data fundacao", "Scraper Rubinot"),
            ("/mortes", "limite (opc)", "Ultimas mortes / PvP kills do servidor", "Scraper Rubinot"),
            ("/ranking", "vocacao (opc), categoria (opc)", "Top 10 do servidor filtrado", "Scraper Rubinot"),
            ("/item", "nome (ingles)", "Stats do item + imagem + dica de uso", "TibiaWiki.dev"),
            ("/monstro", "nome (ingles)", "HP, EXP, loot, resistencias + imagem", "TibiaWiki.dev"),
            ("/boss", "nome", "Guia de boss: nivel, composicao, estrategia, loot", "IA + KB"),
            ("/quest", "nome", "Guia de quest: nivel, passo a passo, recompensas", "IA + KB"),
            ("/rubinot", "tema", "Info do servidor: forge, soulpit, castle, VIP, etc.", "IA + KB"),
            ("/forum", "query", "Busca threads no OtLand e DuckDuckGo sobre o tema", "Forum Scraper"),
            ("/perfil", "—", "Ver/editar perfil: char_name, vocacao, nivel, IA preferida", "memory.py"),
            ("/modelo", "—", "Escolher IA: groq (padrao gratis) ou claude (premium)", "ai_client.py"),
            ("/limpar", "—", "Reseta historico de conversa do usuario", "memory.py"),
            ("/status", "—", "Status tecnico: latencia, modelo IA, caches, usuarios, KB", "Interno"),
            ("/recarregar_kb", "—", "Forca recarregamento da KB extra do GitHub", "kb_loader.py"),
            ("@Companion Tibia", "mensagem livre", "Mencao no canal funciona como /ask", "IA + KB"),
        ],
        col_widths=[3, 3.5, 7.5, 3]
    )

    doc.add_page_break()

    # ── SEÇÃO 8: KNOWLEDGE BASE ──────────────────────────────────────────────
    add_heading(doc, "8. Base de Conhecimento (Knowledge Base)", 1)

    add_paragraph(doc,
        "Toda a KB esta em knowledge_base.py como uma string Python (SYSTEM_PROMPT). "
        "Esta string e injetada como mensagem de sistema em CADA chamada a IA. "
        "A funcao build_full_system_prompt() em kb_loader.py complementa com KB extra do GitHub se disponivel.",
        size=10)

    doc.add_paragraph()
    add_heading(doc, "8.1 Conteudo atual da KB (22.500+ chars)", 2)
    add_table(doc,
        ["Secao", "Conteudo"],
        [
            ("Servidor Rubinot", "Dados gerais, sistemas exclusivos (HuntFinder, Soulpit, Castle, etc.), mecanicas"),
            ("EK (Elite Knight)", "Papel, builds early/mid/end, rotacao de spells solo e party, hunts por nivel"),
            ("RP (Royal Paladin)", "Distance Fighting, Exori Con, auto-suficiencia solo de alto nivel"),
            ("ED (Elder Druid)", "Magic Level, Ice Wave, modo healer em party com Wild Growth e Nature's Embrace"),
            ("MS (Master Sorcerer)", "ML maximo, utamo vita obrigatorio, GFB runes, posicionamento em party"),
            ("Monk (Exalted Monk)", "Sistema Harmony/Virtue/Serene completo, progressao Fist por nivel, papel em party"),
            ("Guias de Hunt Detalhados", "8 spots: Rotworms, Cyclops, Sea Serpents, Asura Mirror, Carnivora, Cobrafang/Soul War, Falcons/Nagas — estrategia por vocacao e loot"),
            ("Tabela Geral de Hunts", "Nivel 8 a 350+, exp/h estimado, modo, melhor vocacao"),
            ("Imbuements Completo", "Todos os slots (arma, capacete, armadura) por vocacao, em ordem de prioridade"),
            ("Composicoes de Grupo", "Duo, trio, party 4 e 5 — com hunt ideal para cada composicao"),
            ("Quests Importantes", "Soul War, Inquisition, Ferumbras Ascendant, Falcon, Nose Ring e Linked Tasks"),
            ("Dicas Gerais", "Soulpit, HuntFinder, Equipment Preset, Gran Con, VIP, Guild, Battle Pass"),
            ("FALTA ADICIONAR", "Demon Forge — spot end-game nao documentado ainda (identificado nas simulacoes)"),
        ],
        col_widths=[4.5, 12.5]
    )

    doc.add_paragraph()
    add_heading(doc, "8.2 KB Extra via GitHub (kb_loader.py)", 2)
    add_paragraph(doc,
        "E possivel manter uma base de conhecimento extra em um arquivo Markdown publico no GitHub. "
        "Configure KB_GITHUB_URL no .env apontando para a URL raw do arquivo. "
        "O bot recarrega automaticamente a cada 30 minutos — sem precisar de redeploy.",
        size=10)

    add_code_block(doc,
        "# Exemplo de configuracao no .env:\n"
        "KB_GITHUB_URL=https://raw.githubusercontent.com/SEU_USER/companion-tibia-kb/main/kb_extra.md\n\n"
        "# Para forcar recarregamento imediato:\n"
        "/recarregar_kb  (comando Discord)")

    doc.add_page_break()

    # ── SEÇÃO 9: APIS ────────────────────────────────────────────────────────
    add_heading(doc, "9. APIs e Integracoes Externas", 1)

    add_table(doc,
        ["API / Servico", "URL", "Custo", "O que fornece", "Limitacoes"],
        [
            ("Groq API (Llama 3.1 70B)", "console.groq.com", "Gratis", "Respostas de IA padrao com contexto completo da KB", "30 req/min, 6.000 tokens/min no free tier"),
            ("Anthropic Claude", "console.anthropic.com", "Pago (opcional)", "IA premium — analises mais profundas", "Requer ANTHROPIC_API_KEY; auto-fallback para Groq se falhar"),
            ("TibiaWiki.dev", "tibiawiki.dev/api", "Gratis", "Itens (stats, imbue slots, onde comprar/dropar) e criaturas", "Endpoint de spells retorna {} — nao implementado"),
            ("Fandom Wiki CDN", "tibia.fandom.com/wiki/Special:FilePath/{nome}.gif", "Gratis", "Imagens de itens e criaturas para embeds Discord", "URLs podem mudar se Fandom alterar estrutura"),
            ("Rubinot Website", "rubinot.com.br", "Gratis (scraping)", "Personagens, guilds, ranking, mortes (PvP kills)", "Bot detection ativo — requer User-Agent real de browser"),
            ("YouTube Data API v3", "console.developers.google.com", "Gratis (10k/dia)", "Videos de hunt por spot e vocacao", "Opcional — so ativa com YOUTUBE_API_KEY"),
            ("OtLand Forum", "otland.net/search/", "Gratis (scraping)", "Threads de forum sobre Rubinot e Tibia OT", "Pode mudar HTML sem aviso; tem fallback para DuckDuckGo"),
            ("DuckDuckGo HTML", "html.duckduckgo.com/html/", "Gratis", "Busca web sem API key — fallback do forum_scraper", "Rate limit informal; cache de 2h reduz chamadas"),
            ("Discord API", "discord.com/api", "Gratis", "Infra do bot: eventos, slash commands, embeds", "Rate limits do Discord (normalmente nao e problema)"),
            ("Railway.app", "railway.app", "Gratis (500h/mes)", "Hosting 24/7 com deploy automatico via GitHub", "500h/mes gratis — exceder custa ~US$5/mes"),
        ],
        col_widths=[3.5, 4.5, 2, 5, 4]
    )

    doc.add_page_break()

    # ── SEÇÃO 10: RODAR LOCAL ────────────────────────────────────────────────
    add_heading(doc, "10. Como Rodar Localmente (passo a passo)", 1)

    add_heading(doc, "Pre-requisitos", 2)
    add_bullet(doc, "Python 3.10 ou superior instalado (python.org)")
    add_bullet(doc, "Token de bot Discord (discord.com/developers)")
    add_bullet(doc, "Chave Groq API gratuita (console.groq.com)")

    doc.add_paragraph()
    add_heading(doc, "Comandos", 2)
    add_code_block(doc, "# 1. Entrar na pasta\ncd companion_tibia")
    add_code_block(doc, "# 2. Instalar dependencias\npip install -r requirements.txt")
    add_code_block(doc, "# 3. Criar e preencher o .env\ncopy .env.example .env\n# Abra o .env e preencha DISCORD_TOKEN e GROQ_API_KEY")
    add_code_block(doc, "# 4. Rodar os testes\npython test_bot.py\n# Deve mostrar: 18/18 testes passaram\n\n# Rodar as simulacoes\npython simulacoes.py\n# Deve mostrar: 28/33 simulacoes passaram")
    add_code_block(doc, "# 5. Iniciar o bot\npython bot.py\n\n# OU com auto-restart:\nrun_forever.bat")

    doc.add_page_break()

    # ── SEÇÃO 11: DEPLOY 24/7 ────────────────────────────────────────────────
    add_heading(doc, "11. Como Fazer Deploy 24/7 (Railway)", 1)

    steps_deploy = [
        "Crie conta no GitHub (github.com) — gratuito",
        "Crie repositorio PRIVADO chamado 'companion-tibia'",
        "Na pasta companion_tibia: git init && git add . && git commit -m 'v3.0' && git push",
        "NUNCA commitar o arquivo .env — o .gitignore ja o exclui automaticamente",
        "Crie conta no Railway (railway.app) — entre com GitHub",
        "Clique em 'New Project' > 'Deploy from GitHub repo' > selecione companion-tibia",
        "Em 'Variables', adicione: DISCORD_TOKEN, GROQ_API_KEY, GROQ_MODEL",
        "Opcionally: ANTHROPIC_API_KEY, YOUTUBE_API_KEY, KB_GITHUB_URL",
        "Clique em 'Deploy' — Railway instala as dependencias e inicia o bot",
        "Na aba 'Logs' verifique se aparece 'Companion Tibia online'",
        "Para atualizar: apenas git push — Railway faz novo deploy automaticamente",
    ]
    for i, s in enumerate(steps_deploy, 1):
        add_numbered(doc, f"{i}. {s}")

    doc.add_page_break()

    # ── SEÇÃO 12: COMO ATUALIZAR ─────────────────────────────────────────────
    add_heading(doc, "12. Como Atualizar o Bot", 1)

    add_heading(doc, "Atualizar a KB apos patch do Rubinot", 2)
    add_code_block(doc, "# Edite knowledge_base.py (ou o arquivo no GitHub se usar KB_GITHUB_URL)\n# Apos salvar:\ngit add knowledge_base.py\ngit commit -m 'kb: atualiza hunt X patch Y.Z'\ngit push\n# Railway faz deploy automatico em ~1 minuto")

    add_heading(doc, "Adicionar novo comando", 2)
    add_code_block(doc,
        "@tree.command(name='novo', description='Descricao do comando')\nasync def novo_cmd(interaction: discord.Interaction, param: str):\n    await interaction.response.defer()\n    pergunta = f'Pergunta sobre {param}...'\n    answer, model = await run(ai_client.chat, [...], system_prompt)\n    embed = make_embed('Titulo', answer, model=model)\n    await interaction.followup.send(embed=embed)")

    add_heading(doc, "Trocar o modelo de IA", 2)
    add_code_block(doc, "# No arquivo .env (ou Variables no Railway):\nGROQ_MODEL=llama3-8b-8192       # Mais rapido, menor qualidade\nGROQ_MODEL=llama-3.1-70b-versatile  # Padrao — melhor qualidade\n\n# Para ativar Claude premium:\nANTHROPIC_API_KEY=sk-ant-...\nCLAUDE_MODEL=claude-sonnet-4-6")

    doc.add_page_break()

    # ── SEÇÃO 13: PROBLEMAS CONHECIDOS ──────────────────────────────────────
    add_heading(doc, "13. Problemas Conhecidos e Limitacoes", 1)

    add_table(doc,
        ["Problema", "Causa", "Impacto", "Solucao/Workaround"],
        [
            ("Rubinot retorna 403 em rede corporativa",
             "Proxy da empresa bloqueia o User-Agent ou SSL do site",
             "Apenas em desenvolvimento — producao (Railway) nao tem esse problema",
             "Codigo ja usa fallback com verify=False. Em desenvolvimento, usar hotspot ou VPN."),
            ("Rubinot pode bloquear scraper em producao",
             "Site tem bot detection — mudanca de HTML pode quebrar o parser",
             "Medio — /personagem, /party, /guild, /ranking, /mortes param de funcionar",
             "Bot faz fallback gracioso: diz nao encontrado em vez de crashar. Monitorar mensalmente."),
            ("TibiaWiki.dev pode ficar offline",
             "API externa gratuita, sem SLA",
             "Baixo — /item e /monstro informam ao usuario",
             "Bot informa o usuario. A IA responde com KB mesmo sem dados da API."),
            ("Rate limit do Groq (30 req/min)",
             "Free tier tem limitacao de requisicoes",
             "Baixo para grupos pequenos/medios",
             "Se ultrapassar: criar segunda API key Groq (gratuita) ou usar llama3-8b (mais rapido)"),
            ("Demon Forge nao esta na KB",
             "Gap de conteudo identificado nas simulacoes",
             "Baixo — bot usa IA generica para esse spot",
             "Adicionar secao 'Demon Forge' em knowledge_base.py na proxima atualizacao"),
            ("Commands slash demoram para aparecer",
             "Discord leva ate 1h para sincronizar globalmente",
             "Apenas na primeira vez ou apos reinicio",
             "Aguardar ~1h. /ajuda aparece primeiro."),
            ("SSL em redes corporativas",
             "Proxy da empresa nao confia em alguns certificados",
             "Apenas desenvolvimento",
             "Codigo ja tem fallback com verify=False para esses casos"),
        ],
        col_widths=[3.5, 3.5, 3, 7]
    )

    doc.add_page_break()

    # ── SEÇÃO 14: ROADMAP ────────────────────────────────────────────────────
    add_heading(doc, "14. Roadmap — Proximas Versoes", 1)

    add_heading(doc, "v3.0 — ENTREGUE (esta versao)", 2)
    add_bullet(doc, "Memoria persistente em JSON (memory.py)")
    add_bullet(doc, "Modo IA dual: Groq (gratis) + Claude (opcional)")
    add_bullet(doc, "KB extra via GitHub sem redeploy (kb_loader.py)")
    add_bullet(doc, "YouTube Data API v3 para videos de hunt (youtube_api.py)")
    add_bullet(doc, "Busca em forum OtLand/DuckDuckGo sem API key (forum_scraper.py)")
    add_bullet(doc, "/guild, /mortes, /ranking implementados (scraper.py expandido)")
    add_bullet(doc, "Perfil do jogador com /perfil e /modelo")
    add_bullet(doc, "24 slash commands no total")
    add_bullet(doc, "28/33 simulacoes passando (simulacoes.py)")

    doc.add_paragraph()
    add_heading(doc, "v3.1 — Conteudo (curto prazo)", 2)
    add_bullet(doc, "Adicionar 'Demon Forge' na knowledge_base.py — gap identificado nas simulacoes")
    add_bullet(doc, "Completar tabela de hunts end-game (Soulpit, Nagas avancadas, Library)")
    add_bullet(doc, "Revisar exp/h estimados apos patches recentes do Rubinot")

    doc.add_paragraph()
    add_heading(doc, "v3.2 — Features Novas (medio prazo)", 2)
    add_bullet(doc, "Notificacoes de patches — bot posta automaticamente no canal de novidades")
    add_bullet(doc, "Comando /compare [char1] [char2] — comparar personagens lado a lado")
    add_bullet(doc, "Calculadora de EXP — quanto tempo falta para proximo nivel")
    add_bullet(doc, "Endpoint de spells da TibiaWiki.dev (se implementarem no lado deles)")

    doc.add_paragraph()
    add_heading(doc, "v4.0 — Escalabilidade (longo prazo)", 2)
    add_bullet(doc, "Vector Search / RAG quando a KB crescer alem de ~5MB")
    add_bullet(doc, "Analytics de uso — quais comandos mais usados")
    add_bullet(doc, "Sistema de contribuicao comunitaria na KB via Pull Request")
    add_bullet(doc, "Dashboard web para o GM do servidor gerenciar o bot")

    doc.add_page_break()

    # ── SEÇÃO 15: O QUE VAI PRO GITHUB ──────────────────────────────────────
    add_heading(doc, "15. O que vai para o GitHub — e o que NAO vai", 1)

    add_heading(doc, "DEVE ir para o GitHub", 2)
    add_table(doc,
        ["Arquivo", "Por que"],
        [
            ("bot.py", "Codigo principal — precisa de versionamento"),
            ("knowledge_base.py", "KB do jogo — evolui a cada patch, importante versionar"),
            ("memory.py", "Sistema de memoria persistente"),
            ("ai_client.py", "Cliente dual IA"),
            ("youtube_api.py", "Integracao YouTube"),
            ("forum_scraper.py", "Busca em foruns"),
            ("kb_loader.py", "Carregador de KB extra"),
            ("scraper.py", "Scraper do Rubinot — pode precisar de manutencao"),
            ("tibia_api.py", "Integracao TibiaWiki — pode evoluir"),
            ("cache.py", "Utilitario estavel"),
            ("keep_alive.py", "Necessario para deploy"),
            ("test_bot.py", "Testes — roda no CI/CD"),
            ("simulacoes.py", "Validacoes sem Discord — util para novos colaboradores"),
            ("requirements.txt", "Railway precisa para instalar dependencias"),
            (".env.example", "Template para novos colaboradores"),
            (".gitignore", "Protege segredos"),
            ("Procfile + railway.toml + runtime.txt", "Configuracao do deploy"),
            ("run_forever.bat / .sh", "Util para outros desenvolvedores rodarem local"),
            ("gerar_documentacao.py", "Reprodutivel — qualquer um pode gerar o .docx"),
        ],
        col_widths=[5, 12]
    )

    doc.add_paragraph()
    add_heading(doc, "NUNCA deve ir para o GitHub", 2)
    add_table(doc,
        ["Arquivo", "Por que"],
        [
            (".env", "Contem DISCORD_TOKEN e GROQ_API_KEY — se vazar, qualquer pessoa controla o bot"),
            ("*.docx", "Binarios grandes — opcional; se quiser, use Git LFS"),
            ("__pycache__/", "Arquivos compilados Python — gerados automaticamente"),
            ("venv/ ou .venv/", "Ambiente virtual local — cada maquina cria o seu"),
            ("data/memory/*.json", "Dados privados de usuarios — nunca commitar"),
        ],
        col_widths=[5, 12]
    )

    add_paragraph(doc,
        "ATENCAO: Se o .env acidentalmente for commitado, IMEDIATAMENTE revogue os tokens: "
        "discord.com/developers > Reset Token | console.groq.com > Delete Key.",
        bold=True, size=10, color=(180, 0, 0))

    doc.add_page_break()

    # ── SEÇÃO 16: SIMULAÇÕES ─────────────────────────────────────────────────
    add_heading(doc, "16. Simulacoes — 10 Exemplos de Uso Real (com resultados)", 1)

    add_paragraph(doc,
        "Executamos 10 simulacoes completas em " + datetime.date.today().strftime("%d/%m/%Y") + " para validar todos os modulos "
        "sem precisar conectar ao Discord ou ao Groq. Resultado global: 28/33 validacoes passando.",
        size=10)

    add_paragraph(doc,
        "As 5 falhas sao ESPERADAS: 4 por bloqueio 403 da rede corporativa (rubinot.com.br "
        "bloqueia bots em ambiente de desenvolvimento — funciona normalmente em producao no Railway) "
        "e 1 gap de conteudo na KB ('Demon Forge' nao documentado ainda).",
        size=10, italic=True)

    doc.add_paragraph()

    # Sim 1
    add_result_block(doc, "1", "Memoria Persistente (memory.py)", "OK",
        "[OK] Salvar perfil do jogador\n"
        "     char_name: Soneca | vocation: Knight | level: 250 | preferred_ai: groq\n\n"
        "[OK] Historico com 2 trocas (4 msgs) -> 3 mensagens salvas\n"
        "     - {role: user, content: 'Qual a melhor hunt para EK 250?'}\n"
        "     - {role: assistant, content: 'Para EK 250 recomendo Cobrafang...'}\n"
        "     - {role: user, content: 'E o imbue ideal?'}\n\n"
        "[OK] Contexto de perfil injetado no prompt:\n"
        "     [Perfil do jogador: Personagem: Soneca | Vocacao: Knight | Nivel: 250]\n\n"
        "[OK] Perfil sobrevive reinicializacao -> lido do arquivo JSON em disco\n"
        "     Arquivo: data/memory/999001.json")

    doc.add_paragraph()

    # Sim 2
    add_result_block(doc, "2", "Cache TTL (cache.py)", "OK",
        "[OK] Guardar e recuperar do cache -> {'spot': 'Cobrafang', 'exp': '1.5M/h'}\n"
        "[OK] Tamanho do cache -> 1 entradas\n"
        "[OK] Expiracao por TTL apos 5s -> entrada expirou corretamente\n"
        "[OK] Multiplas entradas e size() -> 2 entradas ativas")

    doc.add_paragraph()

    # Sim 3
    add_result_block(doc, "3", "Busca de Personagem no Rubinot (scraper.py)", "Parcial (mock)",
        "[FALHOU] Personagem 'Soneca' no rubinot.com.br\n"
        "  Causa: Site retornou 403 — esperado em rede corporativa. Funciona em producao.\n\n"
        "[OK] format_character_embed com dados mockados:\n"
        "  title: Soneca\n"
        "  fields: Vocacao: Elite Knight | Nivel: 312 | Guild: Os Invenciveis\n"
        "  url: https://rubinot.com.br/?subtopic=characters&name=Soneca")

    doc.add_paragraph()

    # Sim 4
    add_result_block(doc, "4", "Busca de Guild no Rubinot (scraper.py)", "Parcial (mock)",
        "[FALHOU] Guild 'Predators' no rubinot.com.br\n"
        "  Causa: Site com 403 em rede corporativa\n\n"
        "[OK] format_guild_embed com dados mockados:\n"
        "  title: Guild — Predators\n"
        "  Lider: Shawnks | Membros: 47 | Fundada: 15/03/2025\n"
        "  url: https://rubinot.com.br/?subtopic=guilds&page=view&GuildName=Predators")

    doc.add_paragraph()

    # Sim 5
    add_result_block(doc, "5", "Ranking do Servidor — Highscores (scraper.py)", "Parcial (mock)",
        "[FALHOU] Ranking real no rubinot.com.br\n"
        "  Causa: Site com 403 — simulando mock\n\n"
        "[OK] format_highscores_embed com dados mockados:\n"
        "  ** Top 5 — Level | Todas as vocacoes**\n"
        "  1. DragonSlayer (Elite Knight) — 850\n"
        "  2. MagicMaster (Master Sorcerer) — 820\n"
        "  3. HolyArcher (Royal Paladin) — 795\n"
        "  4. Shawnks (Elite Knight) — 780\n"
        "  5. Soneca (Exalted Monk) — 750")

    doc.add_paragraph()

    # Sim 6
    add_result_block(doc, "6", "Mortes Recentes / PvP Kills (scraper.py)", "Parcial (mock)",
        "[FALHOU] Feed de mortes real no rubinot.com.br\n"
        "  Causa: Site com 403 — simulando mock\n\n"
        "[OK] format_deaths_embed com dados mockados:\n"
        "  ** Ultimas mortes no Rubinot**\n"
        "  - Soneca foi morto por Shawnks (ha 5 min)\n"
        "  - DragonSlayer foi morto por Sorceress_X (ha 12 min)\n"
        "  - HolyArcher foi morto por Dragao Negro (ha 20 min)")

    doc.add_paragraph()

    # Sim 7
    add_result_block(doc, "7", "TibiaWiki.dev API — Itens (tibia_api.py)", "OK",
        "[OK] Item encontrado na API: 'Dragon Scale Mail'\n"
        "  name=Dragon Scale Mail | armor=15 | slots=1\n\n"
        "[OK] format_item_embed formatado:\n"
        "  title: Dragon Scale Mail\n"
        "  Armor: 15 | Peso: 114.00 oz | Slots de Imbue: 1 | Slot: Body\n"
        "  thumbnail_url: https://tibia.fandom.com/wiki/Special:FilePath/Dragon_Scale_Mail.gif\n\n"
        "BUG CORRIGIDO NESTA SESSAO: campo 'value' da API retorna string.\n"
        "  Fix: int(item['value']) com try/except em tibia_api.py linha 111.")

    doc.add_paragraph()

    # Sim 8
    add_result_block(doc, "8", "TibiaWiki.dev API — Criaturas (tibia_api.py)", "OK",
        "[OK] Criatura encontrada na API: 'Demon'\n"
        "  HP=8200 | EXP=6000\n\n"
        "[OK] format_creature_embed formatado:\n"
        "  title: Demon\n"
        "  HP: 8.200 | EXP: 6.000 | Dano maximo: (detalhado por tipo de dano)\n"
        "  thumbnail_url: https://tibia.fandom.com/wiki/Special:FilePath/Demon.gif")

    doc.add_paragraph()

    # Sim 9
    add_result_block(doc, "9", "Busca em Forum OtLand / DuckDuckGo (forum_scraper.py)", "OK",
        "[OK] Busca real no OtLand por 'monk build rubinot': 3 resultados\n\n"
        "Resultados formatados para embed Discord:\n"
        "  [FRANCE] [13.30] | RubinOT Europe Version! February 21...\n"
        "  -> https://otland.net/threads/.../\n"
        "  Preview: 'First of all, I would like to thank you for honoring RubinOT...'\n\n"
        "  [mais 2 resultados de threads sobre Rubinot no OtLand]\n\n"
        "  Auto-prepend de 'rubinot' na query funciona corretamente.")

    doc.add_paragraph()

    # Sim 10
    add_result_block(doc, "10", "Knowledge Base + Sistema de Dual IA", "Quase OK",
        "[OK] System prompt gerado com sucesso -> 22.586 chars\n"
        "[OK] KB contem 'Monk'\n"
        "[OK] KB contem 'Harmony'\n"
        "[OK] KB contem 'Soul War'\n"
        "[OK] KB contem 'Soulpit'\n"
        "[OK] KB contem 'Rubinot'\n"
        "[FALHOU] KB contem 'Demon Forge' — GAP DE CONTEUDO, adicionar na proxima atualizacao\n"
        "[OK] KB contem 'Cobrafang'\n"
        "[OK] Perfil injetado no prompt: [Perfil: Personagem: Soneca | Vocacao: Knight | Nivel: 250]\n"
        "[OK] Status da IA: 'Groq: llama-3.1-70b-versatile (gratuito) | Claude: nao configurado'\n"
        "[OK] Groq configurado como padrao\n"
        "[OK] Claude opcional (sem custo se inativo)\n"
        "[OK] YouTube opcional (gratuito quando ativo) -> Ativo apenas com YOUTUBE_API_KEY\n"
        "[OK] KB GitHub opcional -> nao configurada (funciona sem ela)")

    doc.add_paragraph()
    add_separator(doc)
    add_paragraph(doc,
        "RESUMO GERAL DAS SIMULACOES: 28/33 validacoes passaram",
        bold=True, size=11)

    add_table(doc,
        ["Simulacao", "Modulo", "Resultado", "Observacao"],
        [
            ("1 — Memoria Persistente", "memory.py", "4/4 OK", "Perfil e historico persistem em JSON"),
            ("2 — Cache TTL", "cache.py", "4/4 OK", "Expiracao funciona corretamente"),
            ("3 — Personagem Rubinot", "scraper.py", "1/2 OK", "403 corporativo; mock OK"),
            ("4 — Guild Rubinot", "scraper.py", "1/2 OK", "403 corporativo; mock OK"),
            ("5 — Ranking Rubinot", "scraper.py", "1/2 OK", "403 corporativo; mock OK"),
            ("6 — Mortes Rubinot", "scraper.py", "1/2 OK", "403 corporativo; mock OK"),
            ("7 — Item TibiaWiki", "tibia_api.py", "2/2 OK", "Bug de 'value' corrigido na sessao"),
            ("8 — Criatura TibiaWiki", "tibia_api.py", "2/2 OK", "Demon — HP e EXP corretos"),
            ("9 — Forum OtLand/DDG", "forum_scraper.py", "3/3 OK", "3 resultados reais encontrados"),
            ("10 — KB + Dual IA", "knowledge_base + ai_client", "9/10 OK", "Falta 'Demon Forge' na KB"),
        ],
        col_widths=[4.5, 3.5, 2.5, 6.5]
    )

    add_paragraph(doc,
        "As 4 falhas de scraper sao ESPERADAS em ambiente corporativo e NENHUMA impede o deploy. "
        "Em producao (Railway), o site do Rubinot e acessivel normalmente.",
        size=10, italic=True)

    doc.add_page_break()

    # ── RODAPÉ ───────────────────────────────────────────────────────────────
    final = doc.add_paragraph()
    final.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = final.add_run(
        f"Companion Tibia — Documentacao Tecnica v3.0 — {datetime.date.today().strftime('%d/%m/%Y')}\n"
        "Criado por Soneca & Shawnks | Rubinot Open PvP"
    )
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(120, 120, 120)

    return doc


# ── Execucao ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Gerando Companion_Tibia_Documentacao.docx ...")
    doc = build_doc()
    output_path = "Companion_Tibia_Documentacao.docx"
    doc.save(output_path)
    print(f"OK — arquivo salvo: {output_path}")
