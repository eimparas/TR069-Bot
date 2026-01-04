#!/usr/bin/env python3

import os
import toml
from modem import modem
import nextcord
from nextcord.ext import commands, tasks
from nextcord.ui import View, button, Button
from datetime import datetime

if os.getenv("CONTAINERIZED"):
    print("App is running containerized!")
    config_filename = "/config/config.cfg"
else:
    config_filename = os.path.join('ModemBot', 'config.cfg')

config_data = {
    'Modem_config': {
        'Host': '',
        'Username': '',
        'Password': '',
        'CpeModel': ''
    },
    'Discord_config': {
        'Api_key': '',
        'Admin_ID': '',
        'Channel_ID': ''
    }
}

# Check if the config file exists
if os.path.isfile(config_filename):
    # Load the config data from the file
    with open(config_filename, 'r') as f:
        config = toml.load(f)

    # Retrieve the information from the config data
    modem_host = config['Modem_config']['Host']
    modem_username = config['Modem_config']['Username']
    modem_password = config['Modem_config']['Password']
    modem_cpe_model = config['Modem_config']['CpeModel']
    
    discord_api_key = config['Discord_config']['Api_key']
    discord_admin_id = config['Discord_config']['Admin_ID']
    discord_channel_id = config['Discord_config']['Channel_ID']

else:
    # Create a config file with placeholders and exit with an error message
    with open(config_filename, 'w') as f:
        toml.dump(config_data, f)

    print(f'Error: {config_filename} not found. A config file with placeholders has been created.')
    exit(1)

def getCPE():
    _modem = None
    brand = modem_cpe_model.lower()
    if brand.__contains__("h267a"):
        _modem = modem.ZTEh267a(modem_host, modem_username, modem_password)
    if brand.__contains__("h1600"):
        _modem = modem.ZTEh1600(modem_host, modem_username, modem_password)
    elif brand.__contains__("technicolor"):
        _modem = modem.TechnicolorModem(modem_host, modem_username, modem_password)
    elif brand.__contains__("openwrt"):
        _modem = modem.OpenWRT(modem_host, modem_username, modem_password)
    return _modem

BOT_TOKEN = discord_api_key
ADMIN_ID = int(discord_admin_id)
CHANNEL_ID = int(discord_channel_id)

print(BOT_TOKEN)
print(ADMIN_ID)
print(CHANNEL_ID)

statusMessage = None
modemStatus = None
intents = nextcord.Intents.default()
intents.message_content = True
client = nextcord.Client(intents=intents)
#client.remove_command("help")

@client.event
async def on_ready():
    print("Ive been attached as '%s'" % client.user)

# @commands.slash_command(name="hello_world", description="Say hello to the world")
# async def hello_world(context, msg: str):
#     await context.respond("Hello, {}".format(msg))

@client.slash_command(name="status", description="Get modem status")
async def status(context: nextcord.Interaction):
    # Immediate response to the interaction
    await context.response.send_message("Fetching modem status... Please wait.", ephemeral=True)

    try:
        # Your modem operations
        modem = getCPE()
        modem.connect()
        modem.updateStats()
        modem.disconnect()

        # Create the embed after fetching data
        view = buttonView(context)
        embed = nextcord.Embed(title="Modem status", color=0x00e600 if modem.isOnline else 0xe60000)
        embed.add_field(name="Line status", value="Online" if modem.isOnline else "Offline")
        embed.add_field(name="FEC errors (U/D)", value="({}, {})".format(modem.fecUP, modem.fecDOWN))
        embed.add_field(name="CRC errors (U/D)", value="({}, {})".format(modem.crcUP, modem.crcDOWN))
        embed.add_field(name="Power (dB) (U/D)", value="({}, {})".format(modem.powerUP, modem.powerDOWN))
        embed.add_field(name="SNR (dB) (U/D)", value="({}, {})".format(modem.snrUP, modem.snrDOWN))
        embed.add_field(name="Attenuation (dB) (U/D)", value="({}, {})".format(modem.attenuationUP, modem.attenuationDOWN))
        embed.add_field(name="Attainable speed (kbps) (U/D)", value="({}, {})".format(modem.attainableUP, modem.attainableDOWN))
        embed.add_field(name="Synchronized speed (kbps) (U/D)", value="({}, {})".format(modem.syncUP, modem.syncDOWN))

        # Follow up with the actual status
        await context.followup.send(embed=embed, view=view)  # Send the final embed
    except Exception as e:
        await context.followup.send(f"An error occurred while fetching the modem status: {str(e)}")


@client.slash_command(name="reboot", description="Reboot the modem")
async def reboot(context: nextcord.Interaction):
    modem = getCPE()
    modem.connect()
    modem.reboot()
    modem.disconnect()
    await context.respond("Modem is rebooting...")

@client.slash_command(name="disconnectline", description="Disconnect the line")
async def disconnectline(context: nextcord.Interaction):
    modem = getCPE()
    modem.connect()
    modem.disconnectLine()
    modem.disconnect()
    await context.respond("Line disconnected")

@client.slash_command(name="connectline", description="Connect the line")
async def connectline(context: nextcord.Interaction):
    modem = getCPE()
    modem.connect()
    modem.connectLine()
    modem.disconnect()
    await context.respond("Line connected")

@tasks.loop(seconds=30)
async def check():
    await client.wait_until_ready()
    print("LINE STATE CHECK")
    global modemStatus
    modem = getCPE()
    modem.connect()
    modem.updateLineState()
    modem.disconnect()
    if modemStatus != modem.isOnline:
        modemStatus = modem.isOnline
        embed = nextcord.Embed(title="Line status change")
        color, response = None, None
        if(modem.isOnline):
            color = 0x00e600
            response = "UP"
        else:
            color = 0xe60000
            response = "DOWN"
        embed.color = color
        embed.description = "Line status changed! Line is **{}**".format(response)
        await client.get_channel(CHANNEL_ID).send("<@{}>".format(ADMIN_ID), embed=embed)


class buttonView(View):
    def __init__(self, context):
        super().__init__()
        self.timeout = None
        self.context = context

    @button(label="UPDATE STATS", emoji="🔄", style=nextcord.ButtonStyle.blurple)
    async def update(self, button: Button, interaction: nextcord.Interaction):
        print("INTERACTION BY %s" % interaction.user)
        try:
            self.context.author = interaction.user
            await interaction.response.defer()  # Slows down interaction, so it won't throw a 404
            embed = await status(self.context, True)
            await interaction.message.edit(embed=embed, view=self)
        except Exception as e:
            print(e)

check.start()
client.run(BOT_TOKEN)