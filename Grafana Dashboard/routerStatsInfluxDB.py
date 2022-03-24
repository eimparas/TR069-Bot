from influxdb import InfluxDBClient
from router import getRouter

modem = getRouter()
client = InfluxDBClient(host="localhost", port=8086, database="modem")

FIELDS = ["FECUP", "FECDOWN", "CRCUP", "CRCDOWN", "SNRUP", "SNRDOWN","ATTUP", "ATTDOWN",
"POWERUP", "POWERDOWN","ATTAINABLEUP", "ATTAINABLEDOWN","MAXUP", "MAXDOWN"]


modem.connect()
modem.updateStats()
data = [modem.stats[0][1], modem.stats[0][0], modem.stats[1][1], modem.stats[1][0],
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

client.write_points([insertionString], protocol="line")
modem.disconnect()
print("Influx database got successfully updated!")
print("Exiting")
client.close()
