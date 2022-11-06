import nextcord
from config import config
from nextcord.ext import commands, tasks
from PfsenseFauxapi.PfsenseFauxapi import PfsenseFauxapi
from requests import get


HOST = config.HOST
KEY = config.KEY
currentIP = ""

SECRET = config.SECRET
client = commands.Bot(command_prefix="$", intents=nextcord.Intents().default())
client.remove_command("help")


@client.event
async def on_ready():
    print("Ive been attached as '%s'" % client.user)


@client.event
async def on_message(message):
    if client.user.mentioned_in(message):
        router = PfsenseFauxapi(HOST, KEY, SECRET)
        gateway = router.gateway_status()
        gatewayStats = list(gateway["data"]["gateway_status"].values())[0]
        RTT = float(gatewayStats["delay"].replace("ms", "")) / 1000
        RTTsd = float(gatewayStats["stddev"].replace("ms", "")) / 1000
        loss = float(gatewayStats["loss"].replace("%", ""))
        embed = nextcord.Embed(
            title="Gateway statistics: ",
            description="RTT: {}ms\nRTTsd: {}ms\nPacketLoss: {}%".format(
                RTT * 1000, RTTsd * 1000, loss
            ),
        )
        await message.channel.send(embed=embed)


@client.command()
async def wanIP(context):
    router = PfsenseFauxapi(HOST, KEY, SECRET)
    gateway = router.gateway_status()
    gatewayStats = list(gateway["data"]["gateway_status"].values())[0]
    IP = gatewayStats["srcip"]
    await context.channel.send(
        embed=nextcord.Embed(
            title="Current pfsense WAN IP address", description=IP, color=0x3730B8
        )
    )


@client.command()
async def gateway(context):
    router = PfsenseFauxapi(HOST, KEY, SECRET)
    gateway = router.gateway_status()
    gatewayStats = list(gateway["data"]["gateway_status"].values())[0]
    RTT = float(gatewayStats["delay"].replace("ms", "")) / 1000
    RTTsd = float(gatewayStats["stddev"].replace("ms", "")) / 1000
    loss = float(gatewayStats["loss"].replace("%", ""))
    embed = nextcord.Embed(
    title="Gateway statistics: ",
        description="RTT: {}ms\nRTTsd: {}ms\nPacketLoss: {}%".format(
            RTT * 1000, RTTsd * 1000, loss
        ),
    )
    await context.channel.send(embed=embed)


@tasks.loop(minutes=10)
async def check():
    await client.wait_until_ready()
    global currentIP
    channel = client.get_channel(config.CHANNEL_ID)
    router = PfsenseFauxapi(HOST, KEY, SECRET)
    gateway = router.gateway_status()
    print("\n GATEWAY STATUS \n\n", router.gateway_status())  # srcip,Delay,loss,status
    gatewayStats = list(gateway["data"]["gateway_status"].values())[0]
    IP = gatewayStats["srcip"]

    PublicIP = get("https://api.ipify.org/").text
    print(IP, PublicIP)
    if IP != PublicIP:  # CGNAT is not allways 100. but definetly has a dif public IP ...
        print("CarierGradeNAT")
        my_embed = nextcord.Embed(title="WARNING", description="CGNAT DETECTED")
        await channel.send("<@{}>".format(config.ADMIN_ID), embed=my_embed)
    else:
        print("publicIP")

    if IP != currentIP:
        ipEmbed = nextcord.Embed(
            title="WAN IP update, new ip: ", description=IP, color=0x12B912
        )
        await channel.send(embed=ipEmbed)
        currentIP = IP


check.start()
client.run(config.BOT_TOKEN)

