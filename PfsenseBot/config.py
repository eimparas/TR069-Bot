import tomllib
import os
import sys

# Check if config file exists
CONFIG_FILE = "config.cfg"

# Pfsense Config
class Config:
    def __init__(self, data):
        self.BOT_TOKEN = data["bot"]["token"]
        self.CHANNEL_ID = data["bot"]["channel_id"]
        self.ADMIN_ID = data["bot"]["admin_id"]
        
        self.HOST = data["pfsense"]["host"]
        self.PFSENSE_USER = data["pfsense"]["user"]
        self.PFSENSE_API_TOKEN = data["pfsense"]["token"]
        self.VERIFY_SSL = data["pfsense"]["verify_ssl"]
        
        self.IP_Check_URLs = data["ip_services"]["urls"]
        
        # Computed property for headers to maintain compatibility or ease of use
        # Based on user feedback: Authorization: Bearer TOKEN and x-api-key: TOKEN work.
        # We will include both to be safe, or just Authorization: Bearer.
        # User example showed: 'Authorization: Bearer ...' and 'x-api-key: ...' with the same token.
        
        self.PFSENSE_HEADERS = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.PFSENSE_API_TOKEN}",
            "x-api-key": self.PFSENSE_API_TOKEN
        }


def load_config(config_file = CONFIG_FILE) -> Config:
    if not os.path.exists(config_file):
        print(f"Error: {config_file} not found. Please create it from the template.")
        sys.exit(1)
    try:
        with open(config_file, "rb") as f:
            data = tomllib.load(f)
        return Config(data)
    except Exception as e:
        print(f"Error loading {config_file}: {e}")
        sys.exit(1)
