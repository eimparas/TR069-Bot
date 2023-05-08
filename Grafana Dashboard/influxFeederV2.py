from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
import modem
import toml
import os

config_filename = 'config.toml'
config_data = {
    'Modem_config': {
        'Host': '',
        'Username': '',
        'Password': '',
        'CpeModel': ''
    },
    'Discord_config': {
        'Api_key': '',
        'Admin_ID': '',
        'Channel_ID': ''
    },
    'Database_Config': {
        'DB_Host': '',
        'DB_Port': '',
        'DB_Token': '',
        'DB_ORG': '',
        'DB_Bucket': ''
    }
}

# Check if the config file exists
if os.path.isfile(config_filename):
    # Load the config data from the file
    with open(config_filename, 'r') as f:
        config = toml.load(f)

    # Retrieve the information from the config data
    modem_host = config['Modem_config']['Host']
    modem_username = config['Modem_config']['Username']
    modem_password = config['Modem_config']['Password']
    modem_cpe_model = config['Modem_config']['CpeModel']
    
    discord_api_key = config['Discord_config']['Api_key']
    discord_admin_id = config['Discord_config']['Admin_ID']
    discord_channel_id = config['Discord_config']['Channel_ID']
    
    db_host = config['Database_Config']['DB_Host']
    db_Port = config['Database_Config']['DB_Port']
    db_Token = config['Database_Config']['DB_Token']
    db_ORG = config['Database_Config']['DB_ORG']
    db_bucket = config['Database_Config']['DB_Bucket']


else:
    # Create a config file with placeholders and exit with an error message
    with open(config_filename, 'w') as f:
        toml.dump(config_data, f)

    print(f'Error: {config_filename} not found. A config file with placeholders has been created.')
    exit(1)



def getCPE():
    _modem = None
    brand = modem_cpe_model.lower()
    if brand.__contains__("zteh267a"):
        _modem = modem.ZTEh267a(modem_host, modem_username, modem_password)
    elif brand.__contains__("technicolor"):
        _modem = modem.TechnicolorModem(modem_host, modem_username, modem_password)
    elif brand.__contains__("openwrt"):
        _modem = modem.OpenWRT(modem_host, modem_username, modem_password)
    return _modem

modem = getCPE()
TOKEN = db_Token
org = db_ORG
bucket = db_bucket


FIELDS = ["FECUP", "FECDOWN", "CRCUP", "CRCDOWN", "SNRUP", "SNRDOWN","ATTUP", "ATTDOWN",
"POWERUP", "POWERDOWN","ATTAINABLEUP", "ATTAINABLEDOWN","MAXUP", "MAXDOWN"]

modem.connect()
modem.updateStats()
data = [modem.fecUP, modem.fecDOWN, modem.crcUP, modem.crcDOWN,
        modem.snrUP, modem.snrDOWN,
        modem.attenuationUP, modem.attenuationDOWN,
        modem.powerUP, modem.powerDOWN,
        modem.attainableUP, modem.attainableDOWN,
        modem.syncUP, modem.syncDOWN]
insertionString = "measurements "

for i in range(len(FIELDS)):
        insertionString = insertionString +"{}={}".format(FIELDS[i], data[i])
        if i != len(FIELDS)-1:
                insertionString = insertionString +","

with InfluxDBClient(url=f"http://{db_host}:{db_Port}", token=TOKEN, org=org) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        write_api.write(bucket, org, insertionString)
modem.disconnect()
print("Influx database got successfully updated!")
#client.close()
