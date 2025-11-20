import discord
import json
import os
from datetime import datetime
from discord import app_commands, Intents, Client, Interaction, Webhook, Permissions

intents = discord.Intents.all()
client = discord.Client(intents=intents, max_messages=10000)
tree = app_commands.CommandTree(client)

TOKEN = os.getenv("TOKEN")

# Load settings from JSON
if os.path.isfile('/config/settings.json'):
    with open("/config/settings.json", "r") as settingsJson:
        settingsData = json.load(settingsJson)
else:
    settingsData = {}

webhooks = {}
DEBUG = False
validSettings = ["WatchedChannel", "PinsChannel"]

# Settings command (allows changing of settings)
@tree.command(name = "settings", description = "Changes settings")
async def settings(interaction, setting: str, channel: str):
    if setting in validSettings:
        try:
            if interaction.guild == None:
                await interaction.response.send_message("Unsupported")
            else:
                settingsData[str(interaction.guild.id)][setting] = channel
        except Exception as e:
            if interaction.guild == None:
                await interaction.response.send_message("Unsupported")
            else:
                settingsData[str(interaction.guild.id)] = {setting:channel}
        with open('/config/settings.json', 'w') as jsonFile:
            json.dump(settingsData, jsonFile)
        await interaction.response.send_message("Setting updated", ephemeral=True)
    else:
        await interaction.response.send_message("Invalid setting", ephemeral=True)

# View Settings command (lists settings)
@tree.command(name = "view_settings", description = "lists settings")
async def view_settings(interaction):
    msgData = "```\n"
    for setting in validSettings:
        try:
            if interaction.guild == None:
                await interaction.response.send_message("Unsupported")
            else:
                msgData = msgData+"\n"+setting+": "+settingsData[str(interaction.guild.id)][setting]
        except Exception as e:
            msgData = msgData+"\n"+setting+": Not Set"
    msgData = msgData+"```"
    await interaction.response.send_message(msgData)

# Export Pins
@tree.command(name = "export_pins", description = "exports pins")
async def export_pins(interaction):
    try:
        print(settingsData[str(interaction.guild_id)]["PinsChannel"])
        if settingsData[str(interaction.guild_id)]["WatchedChannel"] != None and settingsData[str(interaction.guild_id)]["PinsChannel"] != None:
            await interaction.response.send_message("Exporting Pins")
            channel = client.get_channel(int(settingsData[str(interaction.guild_id)]["WatchedChannel"]))
            pins = await channel.pins()
            for m in pins:
                await send_message(m)
        else:
            await interaction.response.send_message("Please set a WatchedChannel and PinnedChannel")
    except Exception as e:
        await interaction.response.send_message("Please set a WatchedChannel and PinnedChannel")


# Get settings
def get_setting(setting, message):
    try:
        return(settingsData[str(message.channel.guild.id)][setting])
    except Exception as e:
        return (False)

# Sends updated message
async def send_message(message):
    try:
        pinchannel = client.get_channel(int(get_setting("PinsChannel", message)))
    except Exception as e:
        return(False)
    if not pinchannel.id in webhooks:
        ### Clears old webhooks from the bot ###
        channel_webhooks = await pinchannel.webhooks() 
        for w in channel_webhooks:
            if w.name == "PinBot":
                await w.delete()
        ### END Clears old webhooks from the bot ###
        webhooks[pinchannel.id] = await pinchannel.create_webhook(name="PinBot")
    # Convert Attachments to Files
    files = []
    curTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for a in message.attachments:
        files.append(await a.to_file())
    embed = discord.Embed(title="Link to message", color=discord.Colour.from_rgb(255, 0, 255), url=message.jump_url)
    try:
        tmpMessage = await webhooks[pinchannel.id].send(files=files, content=message.content, username=message.author.display_name+" ("+curTime+")", avatar_url=message.author.display_avatar, wait=True)
        linkMessage = await webhooks[pinchannel.id].send(embed=embed, username=message.author.display_name+" ("+curTime+")", avatar_url=message.author.display_avatar, wait=True)
        await message.unpin()
    except:
        webhooks[pinchannel.id] = await pinchannel.create_webhook(name="PinBot")
        tmpMessage = await webhooks[pinchannel.id].send(embed = embed, files=files, content=message.content, username=message.author.display_name+" ("+curTime+")", avatar_url=message.author.display_avatar, wait=True)
        linkMessage = await webhooks[pinchannel.id].send(embed=embed, username=message.author.display_name+" ("+curTime+")", avatar_url=message.author.display_avatar, wait=True)
        await message.unpin()
    return(True)

@client.event
async def on_message_edit(before, after):
    if after.pinned:
        if get_setting("WatchedChannel", after):
            if str(after.channel.id) == get_setting("WatchedChannel", after):
                await send_message(after)
        else:
            await after.channel.send("Please set a WatchedChannel and PinnedChannel")

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='Waiting for pins'))
    await tree.sync()
client.run(TOKEN)
