import discord
from discord.ext import commands, tasks
import datetime
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))
ROLE_NAME = os.getenv("ROLE_NAME", "Membro")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    send_war_reminder.start()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    print(f"Mensagem recebida: {message.content} de {message.author}")
    await bot.process_commands(message)

@tasks.loop(hours=24)
async def send_war_reminder():
    now = datetime.datetime.now()
    if now.hour == 18:
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            return
            
        role = discord.utils.get(guild.roles, name=ROLE_NAME)
        if not role:
            return

        mensagem = """📢 **Lembrete – GvG às 20h30**
Pessoal, hoje tem GvG! ⚔️

Quem for participar, esteja online no Discord às 20h30 para organizarmos as PTs e alinharmos a estratégia antes da guerra.

🎯 Vamos em busca de mais uma vitória. Contamos com a presença de todos!"""

        for member in role.members:
            if member.bot:
                continue
            try:
                await member.send(mensagem)
            except discord.Forbidden:
                print(f"Não foi possível enviar DM para {member.name}")

@bot.command()
async def teste_pessoal(ctx):
    mensagem = """📢 **Lembrete – GvG às 20h30**
Pessoal, hoje tem GvG! ⚔️

Quem for participar, esteja online no Discord às 20h30 para organizarmos as PTs e alinharmos a estratégia antes da guerra.

🎯 Vamos em busca de mais uma vitória. Contamos com a presença de todos!"""
    
    try:
        await ctx.author.send(mensagem)
        await ctx.send("✅ Mensagem de teste enviada no seu privado!")
    except discord.Forbidden:
        await ctx.send("❌ Não consegui enviar no seu privado. Verifique suas configurações de DM.")

@bot.command()
async def testar_aviso(ctx):
    if ctx.author.guild_permissions.administrator:
        role = discord.utils.get(ctx.guild.roles, name=ROLE_NAME)
        if not role:
            await ctx.send(f"Cargo '{ROLE_NAME}' não encontrado.")
            return
            
        mensagem = """📢 **Lembrete – GvG às 20h30**
Pessoal, hoje tem GvG! ⚔️

Quem for participar, esteja online no Discord às 20h30 para organizarmos as PTs e alinharmos a estratégia antes da guerra.

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
        await ctx.send(f"Aviso de teste enviado no privado para {count} membros.")
    else:
        await ctx.send("Você não tem permissão para usar este comando.")

bot.run(TOKEN)
