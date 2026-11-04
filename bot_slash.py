import discord
from discord import app_commands
from discord.ext import tasks
import datetime
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))
ROLE_NAME = os.getenv("ROLE_NAME", "Membro")

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f"Bot conectado como {client.user}")
    await tree.sync()
    print("Comandos sincronizados!")
    send_war_reminder.start()

@tasks.loop(hours=1)
async def send_war_reminder():
    now = datetime.datetime.now()
    dia_semana = now.weekday()
    
    if dia_semana in [1, 3, 6] and now.hour == 18:
        guild = client.get_guild(GUILD_ID)
        if not guild:
            return
            
        role = discord.utils.get(guild.roles, name=ROLE_NAME)
        if not role:
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
                print(f"Não foi possível enviar DM para {member.name}")
        print(f"Aviso automático enviado para {count} membros em {now.strftime('%d/%m/%Y %H:%M')}")

@tree.command(name="teste_pessoal", description="Testa o envio da mensagem de guerra no seu privado")
async def teste_pessoal(interaction: discord.Interaction):
    mensagem = """📢 **Lembrete – GvG às 20h30**
Pessoal, hoje tem GvG! ⚔️

Quem for participar, esteja online no Discord às 20h30 para organizarmos as PTs e alinharmos a estratégia antes da guerra.

🎯 Vamos em busca de mais uma vitória. Contamos com a presença de todos!"""
    
    try:
        await interaction.user.send(mensagem)
        await interaction.response.send_message("✅ Mensagem de teste enviada no seu privado!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Não consegui enviar no seu privado. Verifique suas configurações de DM.", ephemeral=True)

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
    await interaction.followup.send(f"✅ Aviso enviado no privado para {count} membros.", ephemeral=True)

client.run(TOKEN)
