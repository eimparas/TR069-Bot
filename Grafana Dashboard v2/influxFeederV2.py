from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from modem import getRouter
import config


TOKEN = config.TOKEN
modem = getRouter()
org = config.INFLUXDB_ORGANIZATION
bucket = config.INFLUXDB_BUCKET


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

with InfluxDBClient(url=f"http://{config.DB_HOST}:{config.DB_PORT}", token=TOKEN, org=org) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        write_api.write(bucket, org, insertionString)
modem.disconnect()
print("Influx database got successfully updated!")
#client.close()
