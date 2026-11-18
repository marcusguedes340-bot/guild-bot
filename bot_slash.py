import sys
sys.stdout.reconfigure(line_buffering=True)
import discord
from discord import app_commands
from discord.ext import tasks
import datetime
import os
from dotenv import load_dotenv
import pytz
import threading
import http.server
import socketserver
import urllib.request
import urllib.parse
import hashlib
import random
import string
import json
import re

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))
ROLE_NAME = os.getenv("ROLE_NAME", "Membro")

print(f"DEBUG STARTUP -> GUILD_ID: {GUILD_ID}, TOKEN present: {bool(TOKEN)}")

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True

port = int(os.environ.get("PORT", 10000))
try:
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
except Exception as e:
    print(f"Web server error: {e}")

intents = discord.Intents.default()
intents.members = True
intents.reactions = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

BID_CHANNEL_ID = 1566888397673603132
HISTORICO_CHANNEL_ID = 1567537503785848992
NEWS_CHANNEL_ID = 1572590362319659108
reaction_messages = {}
historico_messages = {}
posted_news_ids = set()

def fetch_game_news(max_size=5):
    ts = str(int(datetime.datetime.now().timestamp()))
    nonce = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    x_ua = "OS=Win32&LANG=pt&PL=Web&UID=bot&OS=Windows&APP_CODE=1q33ebihjjpucer8"
    params = {
        "X-UA": x_ua,
        "client_id": "fd6f8e433b0acc3a",
        "time": ts,
        "nonce": nonce,
        "max_size": str(max_size),
    }
    pairs = sorted(["%s=%s" % (k, v) for k, v in params.items()])
    param_sign = hashlib.md5(("&".join(pairs) + "dec21f1975d55f8eac64b436c3408210").encode()).hexdigest()
    params["sign"] = param_sign
    qs = "&".join("%s=%s" % (k, urllib.parse.quote(str(v), safe="")) for k, v in params.items())
    path = "/api/config/v1/ops/news"
    hdr_sign = hashlib.md5((path + ts + "B0VwRmcGgKwHmA8zMUgN7g9HJzjBbD5w").encode()).hexdigest()
    req = urllib.request.Request("https://club-api.joymaker.com" + path + "?" + qs, data=b"{}", headers={
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "language": "pt",
        "timestamp": ts,
        "sign": hdr_sign,
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://roocamer.gnjoy.game",
        "Referer": "https://roocamer.gnjoy.game/"
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("data", {}).get("list", [])

def strip_html(text):
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()

@tasks.loop(minutes=30)
async def check_game_news():
    try:
        news_list = fetch_game_news(5)
        news_channel = client.get_channel(NEWS_CHANNEL_ID)
        if not news_channel:
            return
        for item in reversed(news_list):
            item_id = item.get("id")
            if item_id in posted_news_ids:
                continue
            title = item.get("title", "")
            if "notas da atualiza" not in title.lower() and "hotfix" not in title.lower():
                posted_news_ids.add(item_id)
                continue
            category = item.get("category", "news")
            content = strip_html(item.get("content", ""))
            if len(content) > 1500:
                content = content[:1500] + "..."
            created = item.get("created_at", 0)
            created_str = datetime.datetime.fromtimestamp(created, pytz.timezone("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M") if created else "Data desconhecida"
            embed = discord.Embed(title=f"📰 {title}", description=content, color=0x00b0f4)
            embed.set_footer(text=f"Categoria: {category} | {created_str}")
            await news_channel.send(embed=embed)
            posted_news_ids.add(item_id)
            print(f"Noticia publicada: {title}")
    except Exception as e:
        print(f"Erro ao verificar noticias: {e}")

@client.event
async def on_ready():
    print(f"Bot conectado como {client.user} (ID: {client.user.id})")
    print(f"Guild ID configurado: {GUILD_ID}")
    try:
        synced = await tree.sync()
        print(f"Comandos sincronizados ({len(synced)}): {[cmd.name for cmd in synced]}")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")
    if not send_war_reminder.is_running():
        send_war_reminder.start()
    if not keep_alive.is_running():
        keep_alive.start()
    if not check_game_news.is_running():
        check_game_news.start()

@tasks.loop(minutes=5)
async def keep_alive():
    print(f"Bot ativo em {datetime.datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M:%S')} (Horário de Brasília)")

@tasks.loop(minutes=1)
async def send_war_reminder():
    brasilia_tz = pytz.timezone('America/Sao_Paulo')
    now = datetime.datetime.now(brasilia_tz)
    dia_semana = now.weekday()
    
    if dia_semana in [1, 3, 6] and now.hour == 10 and now.minute == 0:
        guild = client.get_guild(GUILD_ID)
        if not guild:
            return
            
        role = discord.utils.get(guild.roles, name=ROLE_NAME)
        if not role:
            return

        mensagem = """📢 **Lembrete – GvG às 20h30**
Pessoal, hoje tem GvG! ⚔️

⚔️ Quem for participar, esteja online no Discord às 20h30 para organizarmos as PTs e alinharmos a estratégia antes da guerra.
⚠️ Quem não for participar, nos deixe avisado no chat #ausencia-guerra para que possamos definir o plantel.

🎯 Vamos em busca de mais uma vitória. Contamos com a presença de todos!"""

        count = 0
        for member in role.members:
            if member.bot:
                continue
            try:
                await member.send(mensagem)
                count += 1
            except discord.Forbidden:
                print(f"Não foi possível enviar DM para {member.name}")
        print(f"Aviso automático enviado para {count} membros em {now.strftime('%d/%m/%Y %H:%M')} (Horário de Brasília)")

@tree.command(name="teste_pessoal", description="Testa o envio da mensagem de guerra no seu privado")
async def teste_pessoal(interaction: discord.Interaction):
    mensagem = """📢 **Lembrete – GvG às 20h30**
Pessoal, hoje tem GvG! ⚔️

⚔️ Quem for participar, esteja online no Discord às 20h30 para organizarmos as PTs e alinharmos a estratégia antes da guerra.
⚠️ Quem não for participar, nos deixe avisado no chat #ausencia-guerra para que possamos definir o plantel.

🎯 Vamos em busca de mais uma vitória. Contamos com a presença de todos!"""
    
    try:
        await interaction.user.send(mensagem)
        await interaction.response.send_message("✅ Mensagem de teste enviada no seu privado!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Não consegui enviar no seu privado. Verifique suas configurações de DM.", ephemeral=True)

@tree.command(name="controle_bid", description="Envia mensagem de controle de BID com reações (Staff)")
async def controle_bid(interaction: discord.Interaction):
    staff_role = discord.utils.get(interaction.guild.roles, name="STAFF")
    if not staff_role or (staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator):
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
        return
    
    bid_channel = client.get_channel(BID_CHANNEL_ID)
    if not bid_channel:
        await interaction.response.send_message("❌ Canal de BID não encontrado.", ephemeral=True)
        return
    
    mensagem = """@everyone

:loudspeaker: **Lembrete – CONTROLE DE BID PROXIMA GUERRA**

:warning: QUEM FOR PARTICIPAR DA GUERRA E DO LEILÃO FAVOR REAGIR AO QUE PRETENDE ENTRAR NA LISTA DE BID:

:warning: MENSAGEM PARA REAÇÃO ATÉ AS 18:00 DO DIA DA GUERRA, QUEM NÃO REAGIR NÃO IRA ENTRAR NA FILA PRA BIDAR

⚪ Plumas Brancas / ⚫ Plumas Pretas / 🃏 Fragmento de Carta Roxa / 🪙 Caixa de Frag Illusional

:dart: Vamos em busca de mais uma vitória. Contamos com a presença de todos!"""
    
    try:
        msg = await bid_channel.send(mensagem, allowed_mentions=discord.AllowedMentions(everyone=True))
        await msg.add_reaction("⚪")
        await msg.add_reaction("⚫")
        await msg.add_reaction("🃏")
        await msg.add_reaction("🪙")
        
        reaction_messages[msg.id] = {
            "⚪": [],
            "⚫": [],
            "🃏": [],
            "🪙": []
        }
        historico_messages[msg.id] = None
        
        await interaction.response.send_message(f"✅ Mensagem de controle de BID enviada em <#{BID_CHANNEL_ID}>!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao enviar mensagem: {str(e)}", ephemeral=True)

@client.event
async def on_raw_reaction_add(payload):
    print(f"Reação detectada: {payload.emoji} por usuário {payload.user_id}")
    
    if payload.user_id == client.user.id:
        return
    
    if payload.message_id not in reaction_messages:
        print(f"Mensagem {payload.message_id} não está sendo rastreada")
        return
    
    emoji = str(payload.emoji)
    if emoji not in ["⚪", "⚫", "🃏", "🪙"]:
        print(f"Emoji {emoji} não é válido")
        return
    
    guild = client.get_guild(payload.guild_id)
    if not guild:
        return
    
    member = guild.get_member(payload.user_id)
    if not member or member.bot:
        return
    
    display_name = member.display_name
    print(f"{display_name} reagiu com {emoji}")
    if display_name not in reaction_messages[payload.message_id][emoji]:
        reaction_messages[payload.message_id][emoji].append(display_name)
        await enviar_historico(payload.message_id)

@client.event
async def on_raw_reaction_remove(payload):
    if payload.message_id not in reaction_messages:
        return
    
    emoji = str(payload.emoji)
    if emoji not in ["⚪", "⚫", "🃏", "🪙"]:
        return
    
    guild = client.get_guild(payload.guild_id)
    if not guild:
        return
    
    member = guild.get_member(payload.user_id)
    if not member or member.bot:
        return
    
    display_name = member.display_name
    if display_name in reaction_messages[payload.message_id][emoji]:
        reaction_messages[payload.message_id][emoji].remove(display_name)
        await enviar_historico(payload.message_id)

async def enviar_historico(message_id):
    historico_channel = client.get_channel(HISTORICO_CHANNEL_ID)
    if not historico_channel:
        return
    
    reactions_data = reaction_messages[message_id]
    brasilia_tz = pytz.timezone('America/Sao_Paulo')
    now = datetime.datetime.now(brasilia_tz)
    
    embed = discord.Embed(
        title="📊 Histórico de Reações - Controle de BID",
        description=f"Atualizado em: {now.strftime('%d/%m/%Y às %H:%M:%S')} (Horário de Brasília)",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.now()
    )
    
    embed.add_field(
        name="⚪ Plumas Brancas",
        value="\n".join(reactions_data["⚪"]) if reactions_data["⚪"] else "Ninguém reagiu ainda",
        inline=False
    )
    
    embed.add_field(
        name="⚫ Plumas Pretas",
        value="\n".join(reactions_data["⚫"]) if reactions_data["⚫"] else "Ninguém reagiu ainda",
        inline=False
    )
    
    embed.add_field(
        name="🃏 Fragmento de Carta Roxa",
        value="\n".join(reactions_data["🃏"]) if reactions_data["🃏"] else "Ninguém reagiu ainda",
        inline=False
    )
    
    embed.add_field(
        name="🪙 Caixa de Frag Illusional",
        value="\n".join(reactions_data["🪙"]) if reactions_data["🪙"] else "Ninguém reagiu ainda",
        inline=False
    )
    
    total = sum(len(v) for v in reactions_data.values())
    embed.set_footer(text=f"Total de participantes: {total}")
    
    if message_id in historico_messages and historico_messages[message_id]:
        try:
            historico_msg = await historico_channel.fetch_message(historico_messages[message_id])
            await historico_msg.edit(embed=embed)
        except:
            historico_msg = await historico_channel.send(embed=embed)
            historico_messages[message_id] = historico_msg.id
    else:
        historico_msg = await historico_channel.send(embed=embed)
        historico_messages[message_id] = historico_msg.id

@tree.command(name="testar_aviso", description="Envia aviso de guerra para todos os membros (Admin)")
async def testar_aviso(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
        return
        
    role = discord.utils.get(interaction.guild.roles, name=ROLE_NAME)
    if not role:
        await interaction.response.send_message(f"❌ Cargo '{ROLE_NAME}' não encontrado.", ephemeral=True)
        return
        
    await interaction.response.defer(ephemeral=True)
    
    mensagem = """📢 **Lembrete – GvG às 20h30**
Pessoal, hoje tem GvG! ⚔️

⚔️ Quem for participar, esteja online no Discord às 20h30 para organizarmos as PTs e alinharmos a estratégia antes da guerra.
⚠️ Quem não for participar, nos deixe avisado no chat #ausencia-guerra para que possamos definir o plantel.

🎯 Vamos em busca de mais uma vitória. Contamos com a presença de todos!"""
    
    count = 0
    for member in role.members:
        if member.bot:
            continue
        try:
            await member.send(mensagem)
            count += 1
        except discord.Forbidden:
            pass
    await interaction.followup.send(f"✅ Aviso enviado no privado para {count} membros.", ephemeral=True)

client.run(TOKEN)
