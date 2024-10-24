import nextcord, time
import os
import toml
from nextcord.ext import tasks, commands
from requests import get
currentIP = ""

intents = nextcord.Intents.default()
intents.message_content = True
#client = commands.Bot(command_prefix='!', intents=intents)
client = nextcord.Client(intents=intents)
config_filename = 'config.cfg'
config_data = {
        'Pfsense': {
            'HOST': '',
            'PFSENSE_USER_ID': '',
            'PFSENSE_API_TOKEN': ''
        },
        'Discord': {
            'CHANNEL_ID': '',
            'ADMIN_ID': '',
            'BOT_TOKEN': ''
        },
        'Remote_Wan': {
            'WanIP_EP': ''
        }
    }

# Check if the config file exists
if os.path.isfile(config_filename):
    # Load the config data from the file
    print("ConfigFound Loading \n")
    with open(config_filename, 'r') as f:
        config = toml.load(f)

    # Read config values into Python variables
    pfsense_Host = config['Pfsense']['HOST']
    pfsense_Token = config['Pfsense']['PFSENSE_API_TOKEN']
    pfsense_UserID = config['Pfsense']['PFSENSE_USER_ID']
    discord_ChannelID = config['Discord']['CHANNEL_ID']
    discord_AdminID = config['Discord']['ADMIN_ID']
    discord_BotToken = config['Discord']['BOT_TOKEN']
    remote_wan = config['Remote_Wan']['WanIP_EP']
else:
    # Create a config file with placeholders and exit with an error message
    with open(config_filename, 'w') as f:
        toml.dump(config_data, f)

    print(f'Error: {config_filename} not found. A config file with placeholders has been created.')
    exit(1)

HEADERS = {"accept": "application/json", "Authorization":f"{pfsense_UserID} {pfsense_Token}"}

@client.event
async def on_ready():
    print("Ive been attached as '%s'" % client.user)
    check.start()

@client.slash_command(name="status", description="Get the current status of pf-sense")
async def wanIPfunction(interaction: nextcord.Interaction):
    print("im called finally")
    pfsense_URL = f"http://{pfsense_Host}/api/v1/status/interface"
    pfAPIResponse = get(pfsense_URL, headers=HEADERS, verify=False).json()
    IP = pfAPIResponse["data"][0]["ipaddr"]
    pfStatus = pfAPIResponse["data"][0]["status"]
    wtfHost = get(remote_wan).json()["YourFuckingHostname"]
    pfgatewayStats = get(f"https://{pfsense_Host}/api/v1/status/gateway", headers=HEADERS, verify=False).json()['data'][0]
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
    channel = client.get_channel(discord_ChannelID)
    wtf = get("https://myip.wtf/json").json()
    PublicIP= wtf["YourFuckingIPAddress"]
    pfsense_URL = f"http://{pfsense_Host}/api/v1/status/interface"
    pfAPIResponse = get(pfsense_URL, headers=HEADERS, verify=False).json()
    IP = pfAPIResponse["data"][0]["ipaddr"]
    if (IP != PublicIP):# CGNAT is not allways 100. but definetly has a dif public IP ...
        print("PANIK")
        my_embed = nextcord.Embed(title="WARNING", description = "CGNAT DETECTED")
        await channel.send("<@{}>".format(discord_AdminID),embed=my_embed)
    else:
        print("KALM")

    if IP != currentIP:
        ipEmbed = nextcord.Embed(title="WAN IP updates , new ip: ", description = IP ,color=0x12B912)
        await channel.send(embed=ipEmbed)##Message location.
        currentIP = IP
client.run(discord_BotToken)
