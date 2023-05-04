import nextcord
import os
import toml
import modem

from nextcord.ext import commands, tasks
from nextcord.ui import View, button, Button
from datetime import datetime

config_filename = 'config.toml'
config_data = {
    'Modem_config': {
        'host': '',
        'username': '',
        'password': '',
        'CpeModel': ''
    },
    'Discord_config': {
        'Api key': '',
        'Admin_ID': '',
        'Channel_ID': ''
    },
    'Database Config': {
        'DB_name': ''
    }
}

# Check if the config file exists
if os.path.isfile(config_filename):
    # Load the config data from the file
    with open(config_filename, 'r') as f:
        config = toml.load(f)

    # Retrieve the information from the config data
    modem_host = config['Modem_config']['host']
    modem_username = config['Modem_config']['username']
    modem_password = config['Modem_config']['password']
    modem_cpe_model = config['Modem_config']['CpeModel']
    
    discord_api_key = config['Discord_config']['Api key']
    discord_admin_id = config['Discord_config']['Admin_ID']
    discord_channel_id = config['Discord_config']['Channel_ID']
    
    db_name = config['Database Config']['DB_name']

else:
    # Create a config file with placeholders and exit with an error message
    with open(config_filename, 'w') as f:
        toml.dump(config_data, f)

    print(f'Error: {config_filename} not found. A config file with placeholders has been created.')
    exit(1)


def getCPE():
    _modem = None
    brand = modem_cpe_model.lower()
    if brand.__contains__("zte"):
        _modem = modem.ZTEh267a(modem_host, modem_username, modem_password)
    elif brand.__contains__("technicolor"):
        _modem = modem.TechnicolorModem(modem_host, modem_username, modem_password)
    elif brand.__contains__("openwrt"):
        _modem = modem.OpenWRT(modem_host, modem_username, modem_password)
    return _modem


BOT_TOKEN = discord_api_key
ADMIN_ID = discord_admin_id
CHANNEL_ID = discord_channel_id


statusMessage = None
modemStatus = None
intents = nextcord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)
client.remove_command("help")


@client.event
async def on_ready():
    print("Ive been attached as '%s'" % client.user)
    
@client.event
async def on_message(message):
    if client.user.mentioned_in(message):
        await message.channel.send("Hiii") #to be continued
    await client.process_commands(message)

@client.command()
async def hello_world(context,*,msg):
    await context.channel.send("Hello, {}".format(msg))

@client.command()
async def status(context, edit=False):
    global statusMessage
    modem = getCPE()
    modem.connect()
    modem.updateStats()
    modem.disconnect()
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
    if edit:
        return embed
    else:
        statusMessage = await context.channel.send(embed=embed, view=view)
    return None

@client.command()
async def reboot(context):
    modem = getCPE()
    modem.connect()
    modem.reboot()
    modem.disconnect()

@client.command()
async def disconnectline(context):
    modem = getCPE()
    modem.connect()
    await context.channel.send("OK!")
    modem.disconnectLine()
    modem.disconnect()

@client.command()
async def connectline(context):
    modem = getCPE()
    modem.connect()
    await context.channel.send("OK!")
    modem.connectLine()
    modem.disconnect()

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
        embed.description  = "Line status changed! Line is **{}**".format(response)
        await client.get_channel(CHANNEL_ID).send("<@{}>".format(ADMIN_ID),embed=embed)

class buttonView(View):
    def __init__(self,context):
        super().__init__()
        self.timeout = None
        self.context = context

    @button(label="UPDATE STATS", emoji="🔄", style=nextcord.ButtonStyle.blurple)
    async def update(self, button: Button, interaction: nextcord.Interaction):
        print("INTERACTION BY %s" % interaction.user)
        try:
            self.context.author = interaction.user
            await interaction.response.defer() #slows down interaction, so it wont throw 404
            embed = await status(self.context, True)
            await interaction.message.edit(embed=embed, view=self)
        except Exception as e:
            print(e)

check.start()
client.run(BOT_TOKEN)
