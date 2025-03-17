import discord
import os
import re
import pytz
from dotenv import load_dotenv
from discord.ext import commands
from datetime import datetime


intents = discord.Intents.default()
intents.members = True  # Pour capturer les changements d'utilisateur
intents.voice_states = True  # Pour les événements des salons vocaux
intents.messages = True  # Pour les événements de messages
intents.message_content = True  # Pour capturer le contenu des messages

load_dotenv()
bot_token = os.getenv('DISCORD_TOKEN')
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID'))

print(f"Token: {bot_token}")  # Affiche le token pour vérifier
print(f"Log Channel ID: {LOG_CHANNEL_ID}")  # Affiche l'ID du channel

if bot_token is None:
    print("Erreur : Token Discord non trouvé.")
if LOG_CHANNEL_ID is None:
    print("Erreur : Log Channel ID non trouvé.")


bot = commands.Bot(command_prefix='!', intents=intents)

# Dictionnaire pour stocker l'heure d'arrivée des membres dans les salons vocaux
user_voice_join_times = {}

@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user}')

@bot.event
async def on_voice_state_update(member, before, after):
    channel = bot.get_channel(LOG_CHANNEL_ID)

    if after.channel is not None and before.channel is None:  # L'utilisateur rejoint un salon vocal
        user_voice_join_times[member.id] = datetime.utcnow()
        embed = discord.Embed(title="Arrivée dans le salon vocal", color=0x3b9c2d)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)  # Photo de profil
        embed.add_field(name="", value=f"📥 {member.mention} a rejoint le salon vocal {after.channel.mention}.", inline=False)
        embed.add_field(name="ID's", value=f"> {member.mention} (`{member.id}`)\n > {after.channel.mention} (`{after.channel.id}`)", inline=False)  # Ici les > sont des markdown
        embed.add_field(name="Salon", value=f"{after.channel.name}", inline=True)
        embed.add_field(name="Heure", value=discord.utils.format_dt(discord.utils.utcnow()), inline=True)  # Heure ajoutée ici
        embed.set_footer(text=f"{bot.user}", icon_url=bot.user.avatar.url)
        await channel.send(embed=embed)

    elif before.channel is not None and after.channel is None:  # L'utilisateur quitte un salon vocal
        join_time = user_voice_join_times.pop(member.id, None)
        duration_str = "Inconnu"
        if join_time:
            # Calcule la durée
            duration = datetime.utcnow() - join_time
            duration_seconds = int(duration.total_seconds())
            hours, remainder = divmod(duration_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            if hours > 0:
                duration_str = f"{hours}h{minutes}m {seconds}s"  # Format avec les heures
            else:
                duration_str = f"{minutes}m {seconds}s"  # Format sans les heures

        embed = discord.Embed(title="Départ du salon vocal", color=0xbb2626)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)  # Photo de profil
        embed.add_field(name="", value=f"📤 {member.mention} a quitté le salon vocal {before.channel.mention}.", inline=False)
        embed.add_field(name="ID's", value=f"> {member.mention} (`{member.id}`)\n > {before.channel.mention} (`{before.channel.id}`)", inline=False)
        embed.add_field(name="Durée de l'appel", value=duration_str, inline=False)
        embed.add_field(name="Salon", value=f"{before.channel.name}", inline=True)
        embed.add_field(name="Heure", value=discord.utils.format_dt(discord.utils.utcnow()), inline=True)  # Heure ajoutée ici
        embed.set_footer(text=f"{bot.user}", icon_url=bot.user.avatar.url)
        await channel.send(embed=embed)

    elif before.channel is not None and after.channel != before.channel:  # Changement de salon vocal
        embed = discord.Embed(title="Changement de salon vocal", color=0x00ff00)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)  # Utilise l'avatar de l'utilisateur
        embed.add_field(name="", value=f"{member.mention} a changé de vocal.", inline=False)
        embed.add_field(name="Salon", value=f"{before.channel.mention} ➡️ {after.channel.mention}", inline=False)  # Mentionne les salons
        embed.add_field(name="ID's", value=f"> {member.mention} (`{member.id}`)\n > {before.channel.mention} (`{before.channel.id}`)\n > {after.channel.mention} (`{after.channel.id}`)", inline=False)
        embed.set_footer(text=f"{bot.user}", icon_url=bot.user.avatar.url)
        await channel.send(embed=embed)

@bot.event
async def on_member_update(before, after):
    try:
        print(f'{before.name} a changé de pseudo, de photo de profil ou de rôles.')
        channel = bot.get_channel(LOG_CHANNEL_ID)

        # Changement de pseudo
        if before.display_name != after.display_name:
            embed = discord.Embed(title="✏️ Changement de pseudo", color=0xaf6e13)
            embed.set_author(name=f"{after.name}", icon_url=after.avatar.url if after.avatar else after.default_avatar.url)
            embed.add_field(name="**Ancien pseudo**", value=f"{before.display_name} ➡️ {after.display_name}", inline=False)
            embed.add_field(name="**Heure du changement**", value=discord.utils.format_dt(discord.utils.utcnow()), inline=True)

            # Récupérer l'utilisateur qui a modifié le pseudo
            audit_logs = after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update)
            modifier = None

            async for log in audit_logs:
                modifier = log.user
                break  # On ne prend que le premier log

            if modifier:
                embed.add_field(
                    name="ID's", 
                    value=(f"> Utilisateur : {after.mention} (`{after.id}`)\n"
                           f"> Modifié par : {modifier.mention} (`{modifier.id}`)"),
                    inline=False
                )
            else:
                embed.add_field(
                    name="ID's", 
                    value=(f"> {after.mention} (`{after.id}`)\n"
                           f"> Modifié par : inconnu"),
                    inline=False
                )

            embed.set_footer(text=f"{bot.user}", icon_url=bot.user.avatar.url)
            await channel.send(embed=embed)

        # Changement de photo de profil
        if before.avatar != after.avatar:
            embed = discord.Embed(title="🖼️ Changement de photo de profil", color=0xff0000)
            embed.add_field(name="Utilisateur", value=f"{after.name}", inline=True)
            embed.set_thumbnail(url=after.avatar.url if after.avatar else None)  # Nouvelle photo de profil
            await channel.send(embed=embed)

        # Changement de rôles
        if before.roles != after.roles:  # Vérifie si les rôles ont changé
            new_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]

            # S'il y a des rôles reçus
            if new_roles:  
                embed = discord.Embed(title="Rôle reçu", color=0x3b9c2d)
                embed.set_author(name=f"{after.name}", icon_url=after.avatar.url if after.avatar else after.default_avatar.url)
                embed.add_field(name="", value=", ".join([role.mention for role in new_roles]), inline=False)

                # Récupérer l'utilisateur qui a attribué le rôle
                audit_logs = after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update)
                modifier = None
                date_assigned = None

                async for log in audit_logs:
                    modifier = log.user
                    date_assigned = log.created_at  # Récupère la date de l'attribution du rôle
                    break  # On ne prend que le premier log

                if modifier:
                    embed.add_field(
                        name="**Date d'attribution**",
                        value=discord.utils.format_dt(date_assigned),
                        inline=False
                    )
                    embed.add_field(
                        name="**ID**", 
                        value=(f"> Utilisateur : {after.mention} (`{after.id}`)\n"
                               f"> Reçu par : {modifier.mention} (`{modifier.id}`)"),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="**Rôle reçu par**", 
                        value="Inconnu",
                        inline=False
                    )

                # Afficher l'avatar et le pseudo de la personne qui a ajouté le rôle
                if modifier:
                    embed.set_footer(text=modifier.name, icon_url=modifier.avatar.url if modifier.avatar else modifier.default_avatar.url)
                else:
                    embed.set_footer(text="Inconnu", icon_url=None)

                await channel.send(embed=embed)

            # S'il y a des rôles retirés
            if removed_roles:
                embed = discord.Embed(title="Rôle retiré", color=0xbb2626)
                embed.set_author(name=f"{after.name}", icon_url=after.avatar.url if after.avatar else after.default_avatar.url)
                embed.add_field(name="", value=", ".join([role.mention for role in removed_roles]), inline=False)

                # Récupérer l'utilisateur qui a retiré le rôle
                audit_logs = after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update)
                modifier = None
                date_removed = None

                async for log in audit_logs:
                    modifier = log.user
                    date_removed = log.created_at  # Récupère la date du retrait du rôle
                    break  # On ne prend que le premier log

                if modifier:
                    embed.add_field(
                        name="**Date de retrait**",
                        value=discord.utils.format_dt(date_removed),
                        inline=False
                    )
                    embed.add_field(
                        name="**ID**", 
                        value=(f"> Utilisateur : {after.mention} (`{after.id}`)\n"
                               f"> Retiré par : {modifier.mention} (`{modifier.id}`)"),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="**Rôle retiré par**", 
                        value="Inconnu",
                        inline=False
                    )

                # Afficher l'avatar et le pseudo de la personne qui a retiré le rôle
                if modifier:
                    embed.set_footer(text=modifier.name, icon_url=modifier.avatar.url if modifier.avatar else modifier.default_avatar.url)
                else:
                    embed.set_footer(text="Inconnu", icon_url=None)

                await channel.send(embed=embed)

    except Exception as e:
        print(f"Une erreur s'est produite : {e}")

@bot.event
async def on_message_delete(message):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel is None:
        print("Erreur : Le salon de logs n'a pas été trouvé.")
        return

    if message.author.bot:
        return  # Ignore les messages des bots

    def replace_custom_emojis(content):
        emoji_pattern = r'<(a?):(\w+):(\d+)>'
        return re.sub(emoji_pattern, lambda m: f"https://cdn.discordapp.com/emojis/{m.group(3)}.{'gif' if m.group(1) == 'a' else 'png'}?size=44&quality=lossless", content)

    embed = discord.Embed(
        title="🗑️ Message supprimé", 
        description=f"Un message a été supprimé dans le salon {message.channel.mention}.",
        color=0xbb2626
    )
    embed.set_author(name=f"{message.author}", icon_url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)

    # Ajout du contenu du message supprimé (si non vide)
    if message.content:
        # Remplacer les emojis personnalisés par leurs liens
        modified_content = replace_custom_emojis(message.content)
        embed.add_field(name="**Contenu du message**", value=modified_content, inline=False)  # Ajout du contenu directement ici
    else:
        embed.add_field(name="**Contenu du message**", value="Message vide ou non-textuel.", inline=False)

    embed.add_field(name="**Heure de suppression**", value=discord.utils.format_dt(discord.utils.utcnow()), inline=True)
    # Bloc ID's regroupé comme pour l'événement vocal
    embed.add_field(
        name="ID's", 
        value=(f"> Message (`{message.id}`)\n"
               f"> {message.channel.mention} (`{message.channel.id}`)\n"
               f"> {message.author.mention} (`{message.author.id}`)"),
        inline=False
    )
    embed.set_footer(text=f"{bot.user}", icon_url=bot.user.avatar.url)

    await channel.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel is None:
        print("Erreur : Le salon de logs n'a pas été trouvé.")
        return

    if before.author.bot or before.content == after.content:
        return
    
    embed = discord.Embed(
        title="📝 Message modifié", 
        description=f"Un message a été modifié dans le salon {before.channel.mention}.",
        color=0xffa500
    )
    
    # Petit avatar à gauche, avec gestion du cas où l'utilisateur n'a pas de photo de profil
    embed.set_author(name=f"{before.author}", icon_url=before.author.avatar.url if before.author.avatar else before.author.default_avatar.url)

    if before.content:
        embed.add_field(name="**Ancien message**", value=before.content, inline=False)
    if after.content:
        embed.add_field(name="**Nouveau message**", value=after.content, inline=False)

    # Heure d'édition
    embed.add_field(name="**Heure**", value=discord.utils.format_dt(discord.utils.utcnow()), inline=True)

    # Bloc ID's avec mentions et IDs comme dans ton exemple
    embed.add_field(
        name="ID's", 
        value=(
            f"> Message (`{before.id}`)\n"  # ID du message avant modification
            f"> {before.channel.mention} (`{before.channel.id}`)\n"  # Mention du salon avec ID
            f"> {before.author.mention} (`{before.author.id}`)"  # Mention de l'utilisateur avec ID
        ),
        inline=False
    )

    # Footer avec avatar du bot
    embed.set_footer(text=f"{bot.user}", icon_url=bot.user.avatar.url)

    await channel.send(embed=embed)

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel is None:
        print("Erreur : Le salon de logs n'a pas été trouvé.")
        return

    # Créer l'embed pour le log
    embed = discord.Embed(
        title="Nouvel utilisateur",
        description=f"📥 {member.mention} a rejoint le serveur.",
        color=0x3b9c2d
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)  # Petit avatar en haut

    # Date de création du compte
    creation_date = member.created_at.strftime("%d %B %Y %H:%M")
    
    # Convertir datetime.utcnow() en timezone UTC
    utc_now = datetime.now(pytz.utc)  # Utiliser pytz pour la conversion

    # Calculer le temps écoulé
    time_elapsed = utc_now - member.created_at
    years, remainder = divmod(time_elapsed.total_seconds(), 31536000)  # 365 jours
    months, _ = divmod(remainder, 2592000)  # 30 jours

    if years > 0:
        time_string = f" (il y a {int(years)} an{'s' if years > 1 else ''})"
    elif months > 0:
        time_string = f" (il y a {int(months)} mois)"
    else:
        time_string = " (il y a moins d'un mois)"

    embed.add_field(name="Création du compte", value=f"{creation_date}{time_string}", inline=False) 

    # Bloc ID's
    embed.add_field(name="ID's", value=f"> <@{member.id}> (`{member.id}`)", inline=False)
    embed.set_footer(text=f"{bot.user}", icon_url=bot.user.avatar.url)

    await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel is None:
        print("Erreur : Le salon de logs n'a pas été trouvé.")
        return

    # Créer l'embed pour le log
    embed = discord.Embed(
        title="Départ utilisateur",
        description=f"📤 {member.mention} a quitté le serveur.",
        color=0xbb2626
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)  # Petit avatar en haut

    # Calculer la durée de présence
    joined_at = member.joined_at
    if joined_at is None:
        time_string = "Durée inconnue."
    else:
        # Convertir joined_at en timezone UTC
        joined_at = joined_at.astimezone(pytz.utc)

        # Utiliser datetime.now(pytz.utc) pour obtenir le temps actuel en UTC
        utc_now = datetime.now(pytz.utc)

        # Calculer le temps écoulé
        time_elapsed = utc_now - joined_at
        days, remainder = divmod(time_elapsed.total_seconds(), 86400)  # 24 heures
        hours, remainder = divmod(remainder, 3600)  # 60 minutes
        minutes, _ = divmod(remainder, 60)  # 60 secondes

        # Construire le message de durée
        parts = []
        if days > 0:
            parts.append(f"{int(days)} jour{'s' if days > 1 else ''}")
        if hours > 0:
            parts.append(f"{int(hours)} heure{'s' if hours > 1 else ''}")
        if minutes > 0:
            parts.append(f"{int(minutes)} minute{'s' if minutes > 1 else ''}")
        time_string = "Membre pendant " + ", ".join(parts) + "."

    embed.add_field(name="Durée sur le serveur", value=time_string, inline=False)

    # Récupérer les rôles
    roles = [role.mention for role in member.roles if role.name != "@everyone"]
    roles_display = ", ".join(roles) if roles else "Aucun rôle"
    embed.add_field(name="Rôles", value=roles_display, inline=False)

    # Bloc ID's
    embed.add_field(name="ID's", value=f"> <@{member.id}> (`{member.id}`)", inline=False)
    embed.set_footer(text=f"{bot.user}", icon_url=bot.user.avatar.url)

    await channel.send(embed=embed)

try:
    bot.run(bot_token)
except Exception as e:
    print(f"Erreur lors du lancement du bot : {e}")