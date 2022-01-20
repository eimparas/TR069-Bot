from pydoc import cli
import nextcord, os, rrdtool, time
from nextcord.ext import commands, tasks
from PfsenseFauxapi.PfsenseFauxapi import PfsenseFauxapi

STAMP = int(time.time())
HOST = "192.168.1.1"
KEY = "PFFAbillySucks"
currentIP = ""
#rrdtool.create("pfsense.rrd", "--start", str(STAMP), "--step", "600",[
#    "DS:RTT:GAUGE:1200:U:U",
#    "DS:RTTSD:GAUGE:1200:U:U",
#    "DS:LOSS:GAUGE:1200:U:U",
#    "DS:STATUS:GAUGE:1200:U:U"
#], "RRA:AVERAGE:0.5:1:2000")
SECRET = "helloiambillyandisuckrealhardhelloiambillyandisuckrealhard"
router = PfsenseFauxapi(HOST, KEY, SECRET)
client = commands.Bot(command_prefix='-', intents=nextcord.Intents().default())
client.remove_command("help")

@client.event
async def on_ready():
    print("Ive been attached as '%s'" % client.user)
    channel = client.get_channel(922896650068967444)
    await channel.send("https://tenor.com/ygkD.gif")

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

@tasks.loop(minutes=10)
async def check():
    print("weeeeeee")
    await client.wait_until_ready()
    global currentIP
    channel = client.get_channel(929455810038358076)
    gateway = router.gateway_status()
    print("\n GATEWAY STATUS \n\n", router.gateway_status())#srcip,Delay,loss,status
    gatewayStats = gateway["data"]["gateway_status"]["1.1.1.1"]
    IP = gatewayStats["srcip"]
    RTT = float(gatewayStats["delay"].replace("ms","")) / 1000
    RTTsd = float(gatewayStats["stddev"].replace("ms", "")) / 1000
    loss = float(gatewayStats["loss"].replace("%",""))
    status = 1 if gatewayStats["status"] == "online" else 0
    if IP.startswith("100."):
        print("PANIK")
        await channel.send("EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEW CGNAT")
    else:
        print("KALM")
        await channel.send("KALM")
    if IP != currentIP:
        await channel.send("IP changed! New IP: {}".format(IP))
        currentIP = IP
    rrdtool.update("pfsense.rrd","{}:{}:{}:{}:{}".format(rrdtool.last("pfsense.rrd")+600, RTT, RTTsd
    ,loss, status))        
    print(IP, RTT, RTTsd,loss, status) #JSON MY LOVExmlllllll

def graph(name):
    rrdtool.graph("{}.png".format(name),
        "--start", str(STAMP), "--end", str(rrdtool.last("pfsense.rrd")),"--watermark=LRRLI LARLOM",
        "DEF:line=pfsense.rrd:{}:AVERAGE".format(name),
        "LINE1:line#FF0000:{}".format(name),)

check.start()
client.run("OTMzNTA4NzQ2MTk2NDQzMTc3.YeijxA.G2VutX_W8nuKpkp4odHJ-Wuh2CY")