import nextcord, rrdtool, time
from nextcord.ext import commands, tasks
from nextcord.ui import View, button, Button
from router import getRouter
from datetime import datetime
from config import BOT_TOKEN, ADMIN_ID, CHANNEL_ID
from os.path import exists


stamp = int(time.time())

if not exists("test.rrd"):
    rrdtool.create("test.rrd", "--start", str(stamp),"--step","600", 
    ["DS:FECUP:GAUGE:1200:U:U","DS:FECDOWN:GAUGE:1200:U:U",
    "DS:CRCUP:GAUGE:1200:U:U","DS:CRCDOWN:GAUGE:1200:U:U",
    "DS:SNRUP:GAUGE:1200:U:U", "DS:SNRDOWN:GAUGE:1200:U:U",
    "DS:ATTUP:GAUGE:1200:U:U", "DS:ATTDOWN:GAUGE:1200:U:U",
    "DS:POWERUP:GAUGE:1200:U:U", "DS:POWERDOWN:GAUGE:1200:U:U",
    "DS:ATTAINABLEUP:GAUGE:1200:U:U", "DS:ATTAINABLEDOWN:GAUGE:1200:U:U",
    "DS:MAXUP:GAUGE:1200:U:U", "DS:MAXDOWN:GAUGE:1200:U:U",
    ],
    "RRA:AVERAGE:0.5:1:2000")
    print("TEST RRD CREATED")

if not exists("dailies.rrd"):
    rrdtool.create("dailies.rrd","--start", str(stamp), "--step","86400",
    ["DS:DAILYFECUP:GAUGE:100000:U:U", "DS:DAILYFECDOWN:GAUGE:100000:U:U",
    "DS:DAILYCRCUP:GAUGE:100000:U:U", "DS:DAILYCRCDOWN:GAUGE:100000:U:U"],
    "RRA:AVERAGE:0.5:1:100")
    print("DAILIES RRD CREATED")
    
STATS = ["FECUP", "FECDOWN", "CRCUP", "CRCDOWN", "SNRUP", "SNRDOWN","ATTUP", "ATTDOWN",
"POWERUP", "POWERDOWN","ATTAINABLEUP", "ATTAINABLEDOWN","MAXUP", "MAXDOWN"]

DAILYSTATS = ["DAILYFECUP", "DAILYFECDOWN","DAILYCRCUP","DAILYCRCDOWN"]

statusMessage = None
modemStatus = None
day = datetime.today().day
client = commands.Bot(command_prefix="!", intents=nextcord.Intents().default())
client.remove_command("help")


@client.event
async def on_ready():
    print("Ive been attached as '%s'" % client.user)
    #channel = client.get_channel(CHANNEL_ID)
    #await channel.send("https://tenor.com/ygkD.gif ")

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
    router = getRouter()
    router.connect()
    router.updateStats()
    router.disconnect()
    view = buttonView(context)
    embed = nextcord.Embed(title="TG-789 status", color=0x00e600 if router.isOnline else 0xe60000)
    embed.add_field(name="Line status", value="Online" if router.isOnline else "Offline")
    embed.add_field(name="FEC errors (U/D)", value="({}, {})".format(router.stats[0][1], router.stats[0][0]))
    embed.add_field(name="CRC errors (U/D)", value="({}, {})".format(router.stats[1][1], router.stats[1][0]))
    embed.add_field(name="Power (dB) (U/D)", value="({}, {})".format(router.powerUP, router.powerDOWN))
    embed.add_field(name="SNR (dB) (U/D)", value="({}, {})".format(router.snrUP, router.snrDOWN))
    embed.add_field(name="Attenuation (dB) (U/D)", value="({}, {})".format(router.attenuationUP, router.attenuationDOWN))
    embed.add_field(name="Attainable speed (kbps) (U/D)", value="({}, {})".format(router.attainableUP, router.attainableDOWN))
    embed.add_field(name="Synchronized speed (kbps) (U/D)", value="({}, {})".format(router.syncUP, router.syncDOWN))
    if edit:
        return embed
    else:
        statusMessage = await context.channel.send(embed=embed, view=view)
    return None

@client.command()
async def CRC(context,*,msg=""):
    interval = None
    if "hour" in msg:
        interval = 6 #6*10 mins = 1 hour
    await sendPlots("CRC", context, "test.rrd", interval)

@client.command()
async def FEC(context,*,msg=""):
    interval = None
    if "hour" in msg:
        interval = 6 #6*10 mins = 1 hour
    await sendPlots("FEC", context, "test.rrd", interval)

@client.command()
async def SNR(context,*,msg=""):
    interval = None
    if "hour" in msg:
        interval = 6 #6*10 mins = 1 hour
    await sendPlots("SNR", context, "test.rrd", interval)

@client.command()
async def PWR(context,*,msg=""):
    interval = None
    if "hour" in msg:
        interval = 6 #6*10 mins = 1 hour
    await sendPlots("POWER", context, "test.rrd", interval)


@client.command()
async def ATT(context,*,msg=""):
    interval = None
    if "hour" in msg:
        interval = 6 #6*10 mins = 1 hour
    await sendPlots("ATT", context, "test.rrd", interval)

@client.command()
async def ATTAINABLE(context,*,msg=""):
    interval = None
    if "hour" in msg:
        interval = 6 #6*10 mins = 1 hour
    await sendPlots("ATTAINABLE", context, "test.rrd", interval)

@client.command()
async def MAX(context,*,msg=""):
    interval = None
    if "hour" in msg:
        interval = 6 #6*10 mins = 1 hour
    await sendPlots("MAX", context, "test.rrd", interval)

@client.command()
async def DAILYFEC(context):
    await sendPlots("DAILYFEC", context, "dailies.rrd")

@client.command()
async def DAILYCRC(context):
    await sendPlots("DAILYCRC", context,"dailies.rrd")

@client.command()
async def reboot(context):
    modem = getRouter()
    modem.connect()
    modem.reboot()
    modem.disconnect()

@tasks.loop(minutes=10)
async def check():
    await client.wait_until_ready()
    print("UPDATING CHECK")
    modem = getRouter()
    modem.connect()
    modem.updateStats()
    #modem.showStats()
    rrdtool.update("test.rrd","N:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}".format(
        modem.stats[0][1], modem.stats[0][0], modem.stats[1][1], modem.stats[1][0],
        modem.snrUP, modem.snrDOWN,
        modem.attenuationUP, modem.attenuationDOWN,
        modem.powerUP, modem.powerDOWN,
        modem.attainableUP, modem.attainableDOWN,
        modem.syncUP, modem.syncDOWN,
    ))
    modem.showStats()
    global day, modemStatus
    dayNow = datetime.today().day
    if dayNow != day:
        print("UPDATING DAILIES")
        day = dayNow
        modem.showStats()
        rrdtool.update("dailies.rrd", "N:{}:{}:{}:{}".format(
        modem.lastDayStats[0][1], modem.lastDayStats[0][0],
        modem.lastDayStats[1][1], modem.lastDayStats[1][0]))
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
    
    #updateCSVHistoryFiles(modem)
    modem.disconnect()

def graph(graph_name, file, interval=None):
    label = " "
    startingPoint= rrdtool.first(file)
    if interval is not None:
        startingPoint = int(rrdtool.last(file)) - interval*600
    if "ATT" in graph_name or "POWER" in graph_name or "SNR" in graph_name:
        label = "{} (dB)".format(graph_name)
    if "ATTAINABLE" in graph_name or "MAX" in graph_name:
        label = "{} (kbps)".format(graph_name)
    rrdtool.graph("{}.png".format(graph_name),
        "--start", str(startingPoint), "--end", str(rrdtool.last(file)),"--watermark=LRRLI LARLOM",
        "DEF:line={}:{}:AVERAGE".format(file,graph_name),
        "LINE1:line#FF0000:{}".format(graph_name),
        "--week-fmt","%d:%m:%Y", "--vertical-label", label)



async def sendPlots(graphName,context,dbfile, interval=None):
    graph("{}UP".format(graphName),dbfile, interval)
    embedUP = nextcord.Embed(title="{} Upstream".format(graphName), color=0x00e600)
    embedUP.set_image(url="attachment://{}UP.png".format(graphName))
    await context.channel.send(file=nextcord.File("{}UP.png".format(graphName)), embed=embedUP)
    graph("{}DOWN".format(graphName), dbfile, interval)
    embedDOWN = nextcord.Embed(title="{} Downstream".format(graphName), color=0xe60000)
    embedDOWN.set_image(url="attachment://{}DOWN.png".format(graphName))
    await context.channel.send(file=nextcord.File("{}DOWN.png".format(graphName)), embed=embedDOWN)

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