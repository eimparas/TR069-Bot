import nextcord, time
from config import config
from nextcord.ext import tasks
from requests import get
currentIP = ""


HEADERS = {"accept": "application/json", "Authorization":f"{config.PFSENSE_USER_ID} {config.PFSENSE_API_TOKEN}"}
intents = nextcord.Intents.default()
intents.message_content = True
#client = commands.Bot(command_prefix='!', intents=intents)
client = nextcord.Client(intents=intents)

@client.event
async def on_ready():
    print("Ive been attached as '%s'" % client.user)
    check.start()
    
@client.slash_command(name="status", description="Get the current status of pf-sense")
async def wanIPfunction(interaction: nextcord.Interaction):
    print("im called finally")
    pfsense_URL = f"http://{config.HOST}/api/v1/status/interface"
    pfAPIResponse = get(pfsense_URL, headers=HEADERS, verify=False).json()
    IP = pfAPIResponse["data"][0]["ipaddr"]
    pfStatus = pfAPIResponse["data"][0]["status"]
    wtfHost = get("https://myip.wtf/json").json()["YourFuckingHostname"]
    pfgatewayStats = get(f"https://{config.HOST}/api/v1/status/gateway", headers=HEADERS, verify=False).json()['data'][0]
    rtt = pfgatewayStats['delay']
    rttsd = pfgatewayStats['stddev']
    loss = pfgatewayStats['loss']
    embed = nextcord.Embed(title="Pf-sense WAN", description=f"**-Status: **{pfStatus}\n**-IP address:** {IP}\n**-FQDN:** {wtfHost}\n**-RTT**: {rtt} ms\n**-RTTsd: **{rttsd} ms\n**-LOSS :**{loss}%", 
        color=0x3730b8)
    await interaction.response.send_message(embed=embed)

@tasks.loop(minutes=10)
async def check():
    print("PfsenseBot Runing")
    global currentIP
    channel = client.get_channel(config.CHANNEL_ID)
    wtf = get("https://myip.wtf/json").json()
    PublicIP= wtf["YourFuckingIPAddress"]
    pfsense_URL = f"http://{config.HOST}/api/v1/status/interface"
    pfAPIResponse = get(pfsense_URL, headers=HEADERS, verify=False).json()
    IP = pfAPIResponse["data"][0]["ipaddr"]
    if (IP != PublicIP):# CGNAT is not allways 100. but definetly has a dif public IP ...
        print("PANIK")
        my_embed = nextcord.Embed(title="WARNING", description = "CGNAT DETECTED")
        await channel.send("<@{}>".format(config.ADMIN_ID),embed=my_embed)
    else:
        print("KALM")
        
    if IP != currentIP:
        ipEmbed = nextcord.Embed(title="WAN IP updates , new ip: ", description = IP ,color=0x12B912)
        await channel.send(embed=ipEmbed)##Message location. 
        currentIP = IP
client.run(config.BOT_TOKEN)
