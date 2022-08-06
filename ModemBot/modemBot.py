import nextcord, config
from nextcord.ext import commands, tasks
from nextcord.ui import View, button, Button
from modem import TechnicolorModem
from datetime import datetime

HOST = config.HOST
USERNAME = config.USERNAME
PASSWORD = config.PASSWORD
BOT_TOKEN = config.BOT_TOKEN
ADMIN_ID = config.ADMIN_ID
CHANNEL_ID = config.CHANNEL_ID


statusMessage = None
modemStatus = None
client = commands.Bot(command_prefix="!", intents=nextcord.Intents().default())
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
    modem = TechnicolorModem(HOST, USERNAME, PASSWORD)
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
    modem = TechnicolorModem(HOST, USERNAME, PASSWORD)
    modem.connect()
    modem.reboot()
    modem.disconnect()

@client.command()
async def disconnectline(context):
    modem = TechnicolorModem(HOST, USERNAME, PASSWORD)
    modem.connect()
    await context.channel.send("OK!")
    modem.disconnectLine()
    modem.disconnect()

@client.command()
async def connectline(context):
    modem = TechnicolorModem(HOST, USERNAME, PASSWORD)
    modem.connect()
    await context.channel.send("OK!")
    modem.connectLine()
    modem.disconnect()

@tasks.loop(seconds=30)
async def check():
    await client.wait_until_ready()
    print("LINE STATE CHECK")
    global modemStatus
    modem = TechnicolorModem(HOST, USERNAME, PASSWORD)
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