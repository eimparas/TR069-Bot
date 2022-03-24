import nextcord, config, rrdtool, time
from nextcord.ext import commands, tasks
from PfsenseFauxapi.PfsenseFauxapi import PfsenseFauxapi
from requests import get
from os import exist

STAMP = int(time.time())
HOST = config.HOST
KEY = config.KEY
currentIP = ""

if not exist("pfsense.rrd"):
    rrdtool.create("pfsense.rrd", "--start", str(STAMP), "--step", "600",[
        "DS:RTT:GAUGE:1200:U:U",
        "DS:RTTSD:GAUGE:1200:U:U",
        "DS:LOSS:GAUGE:1200:U:U",
        "DS:STATUS:GAUGE:1200:U:U"
    ],  "RRA:AVERAGE:0.5:1:2000")
    
SECRET = config.SECRET
client = commands.Bot(command_prefix='!', intents=nextcord.Intents().default())
client.remove_command("help")

@client.event
async def on_ready():
    print("Ive been attached as '%s'" % client.user)
    #channel = client.get_channel(config.CHANNEL_ID)
    #await channel.send("https://tenor.com/ygkD.gif")

@client.command()
async def hello_world(context,*,msg):
    await context.channel.send("Hello, {}".format(msg))

@client.command()
async def RTT(context):
    graph("RTT")
    await context.channel.send(file= nextcord.File("RTT.png"))
    

@client.command()
async def RTTsd(context):
    graph("RTTSD")
    await context.channel.send(file= nextcord.File("RTTSD.png"))
    

@client.command()
async def LOSS(context):
    graph("LOSS")
    await context.channel.send(file= nextcord.File("LOSS.png"))
    

@client.command()
async def STATUS(context):
    graph("STATUS")
    await context.channel.send(file= nextcord.File("STATUS.png"))

@client.command()
async def wanIP(context):
    router = PfsenseFauxapi(HOST, KEY, SECRET)
    gateway = router.gateway_status()
    gatewayStats = gateway["data"]["gateway_status"][list(gateway["data"]["gateway_status"].keys())[0]]
    IP = gatewayStats["srcip"]
    await context.channel.send(embed=nextcord.Embed(title="Current pfsense WAN IP address", description=IP, color=0x3730b8))

@tasks.loop(minutes=10)
async def check():
    print("weeeeeee")
    await client.wait_until_ready()
    global currentIP
    channel = client.get_channel(config.CHANNEL_ID)
    router = PfsenseFauxapi(HOST, KEY, SECRET)
    gateway = router.gateway_status()
    print("\n GATEWAY STATUS \n\n", router.gateway_status())#srcip,Delay,loss,status
    gatewayStats = gateway["data"]["gateway_status"][list(gateway["data"]["gateway_status"].keys())[0]]
    IP = gatewayStats["srcip"]
    RTT = float(gatewayStats["delay"].replace("ms","")) / 1000
    RTTsd = float(gatewayStats["stddev"].replace("ms", "")) / 1000
    loss = float(gatewayStats["loss"].replace("%",""))
    status = 1 if gatewayStats["status"] == "online" else 0
    PublicIP= get("https://api.ipify.org/").text
    
    if (IP != PublicIP):# CGNAT is not allways 100. but definetly has a dif public IP ...
        print("PANIK")
        my_embed = nextcord.Embed(title="WARNING", description = "CGNAT DETECTED")
        await channel.send("<@{}>".format(config.ADMIN_ID),embed=my_embed)
    else:
        print("KALM")
        #await channel.send("kalm")
    if IP != currentIP:
        ipEmbed = nextcord.Embed(title="WAN IP updates , new ip: ", description = IP ,color=0x12B912)
        await channel.send(embed=ipEmbed)##Message location. 
        currentIP = IP
    rrdtool.update("pfsense.rrd","{}:{}:{}:{}:{}".format(rrdtool.last("pfsense.rrd")+600, RTT, RTTsd
    ,loss, status))        
    print(IP, RTT, RTTsd,loss, status)

def graph(name):
    rrdtool.graph("{}.png".format(name),
        "--start", str(STAMP), "--end", str(rrdtool.last("pfsense.rrd")),"--watermark=LRRLI LARLOM",
        "DEF:line=pfsense.rrd:{}:AVERAGE".format(name),
        "LINE1:line#FF0000:{}".format(name),)

check.start()
client.run(config.BOT_TOKEN)