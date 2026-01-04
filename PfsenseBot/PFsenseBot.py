#!/usr/bin/env python3

import nextcord
import asyncio
import aiohttp
import logging
import json
import os
from datetime import datetime
from nextcord.ext import tasks
from PfsenseBot.config import load_config

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pfsense_bot.log")
    ]
)
logger = logging.getLogger("PfsenseBot")

# --- persistence ---
STATE_FILE = "state.json"
CONFIG = load_config(os.path.join("PfsenseBot", "config.cfg"))

class BotState:
    def __init__(self):
        self.current_ip = ""
        self.load()

    def load(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    data = json.load(f)
                    self.current_ip = data.get("current_ip", "")
                logger.info(f"State loaded. Last known IP: {self.current_ip}")
            except Exception as e:
                logger.error(f"Failed to load state: {e}")

    def save(self):
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump({"current_ip": self.current_ip}, f)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

bot_state = BotState()

# --- Async Helper Functions ---

async def fetch_url(session, url, headers=None, verify_ssl=True):
    """Generic async fetcher with error handling."""
    try:
        async with session.get(url, headers=headers, ssl=verify_ssl, timeout=10) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.warning(f"Request to {url} failed with status {response.status}")
                return None
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None

async def get_public_ip(session):
    """Try multiple services to get public IP."""
    for url in CONFIG.IP_Check_URLs:
        data = await fetch_url(session, url)
        if data:
            # Handle different API formats
            if "YourFuckingIPAddress" in data: # myip.wtf
                return data["YourFuckingIPAddress"]
            if "ip" in data: # ipify
                return data["ip"]
            if "ip_addr" in data: # ifconfig.me
                return data["ip_addr"]
            # Fallback for plain json {"ip": "..."}
            return data.get("ip") or data.get("address")
    logger.error("All IP check services failed.")
    return None

async def get_pfsense_wan_ip(session):
    """Get WAN IP from pfSense."""
    # v2 Endpoint
    url = f"https://{CONFIG.HOST}/api/v2/status/interfaces"
    if not CONFIG.VERIFY_SSL:
        pass
        
    data = await fetch_url(session, url, headers=CONFIG.PFSENSE_HEADERS, verify_ssl=CONFIG.VERIFY_SSL)
    if data and "data" in data and len(data["data"]) > 0:
        # Loop through interfaces to find WAN
        for iface in data["data"]:
            # Check for 'wan' name or description containing WAN
            if iface.get("name") == "wan" or "WAN" in iface.get("descr", ""):
                return iface.get("ipaddr")
        # Fallback to first iface if WAN not found specifically
        return data["data"][0].get("ipaddr")
    return None

async def get_gateway_stats(session):
    """Get Gateway stats."""
    # v2 Endpoint
    url = f"https://{CONFIG.HOST}/api/v2/status/gateways"
    data = await fetch_url(session, url, headers=CONFIG.PFSENSE_HEADERS, verify_ssl=CONFIG.VERIFY_SSL)
    if data and "data" in data and len(data["data"]) > 0:
        return data["data"][0]
    return None

# --- Bot Setup ---
intents = nextcord.Intents.default()
intents.message_content = True
client = nextcord.Client(intents=intents)

@client.event
async def on_ready():
    logger.info(f"Bot is ready as '{client.user}'")
    check_loop.start()

@client.slash_command(name="status", description="Get the current status of pfSense")
async def status_command(interaction: nextcord.Interaction):
    logger.info(f"Command 'status' called by {interaction.user}")
    await interaction.response.defer() # Defer incase API is slow

    async with aiohttp.ClientSession() as session:
        # Run fetches in parallel for speed
        pfsense_ip_task = asyncio.create_task(get_pfsense_wan_ip(session))
        gateway_stats_task = asyncio.create_task(get_gateway_stats(session))
        
        # We can also get public IP/Hostname if needed, preserving original logic
        # Original used myip.wtf for hostname
        hostname_task = fetch_url(session, "https://myip.wtf/json")

        wan_ip = await pfsense_ip_task
        stats = await gateway_stats_task
        whoami = await hostname_task
        
    if not wan_ip:
        await interaction.followup.send("❌ Failed to reach pfSense or retrieve WAN IP.")
        return

    # Process data
    pf_status = "Online" # If we got data, it's online-ish. Original code assumed status from API.
    # Actually API returns status in interface stats, let's look closer if we had the full response
    # For now, let's stick to what we retrieved.
    
    hostname = whoami.get("YourFuckingHostname", "Unknown") if whoami else "Unknown"
    
    rtt = stats.get('delay', 'N/A') if stats else 'N/A'
    rttsd = stats.get('stddev', 'N/A') if stats else 'N/A'
    loss = stats.get('loss', 'N/A') if stats else 'N/A'
    
    embed = nextcord.Embed(
        title="pfSense WAN Status",
        description=f"**-IP address:** {wan_ip}\n **-FQDN:** {hostname}\n **-RTT:** {rtt}\n **-RTTsd:** {rttsd}\n **-LOSS:** {loss}",
        color=0x3730b8
    )
    await interaction.followup.send(embed=embed)

@tasks.loop(minutes=10)
async def check_loop():
    logger.info("Running periodic check...")
    channel = client.get_channel(CONFIG.CHANNEL_ID)
    if not channel:
        logger.warning(f"Channel {CONFIG.CHANNEL_ID} not found.")
        return

    async with aiohttp.ClientSession() as session:
        public_ip = await get_public_ip(session)
        wan_ip = await get_pfsense_wan_ip(session)

    if not wan_ip:
        logger.warning("Could not retrieve WAN IP from pfSense.")
        return

    # Check for CGNAT (WAN IP != Public IP)
    if public_ip and wan_ip != public_ip:
        logger.warning(f"CGNAT Detected. WAN: {wan_ip}, Public: {public_ip}")
        embed = nextcord.Embed(title="WARNING", description="🚨 🚨 CGNAT DETECTED 🚨 🚨 ", color=0xFF0000)
        await channel.send(f"<@{CONFIG.ADMIN_ID}>", embed=embed)
    
    # Check for IP Change
    if bot_state.current_ip and wan_ip != bot_state.current_ip:
        logger.info(f"WAN IP Changed from {bot_state.current_ip} to {wan_ip}")
        embed = nextcord.Embed(title="WAN IP Updated", description=f"New IP: {wan_ip}", color=0x12B912)
        await channel.send(embed=embed)
        bot_state.current_ip = wan_ip
        bot_state.save()
    elif not bot_state.current_ip:
        # First run, just save it
        logger.info(f"First run. Saving IP: {wan_ip}")
        bot_state.current_ip = wan_ip
        bot_state.save()

client.run(CONFIG.BOT_TOKEN)