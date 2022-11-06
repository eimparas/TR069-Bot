## Instalation instructions for Grafana modem dashboard.
> Documentation and a step-by-step guide on how to prepare a debian/debian like machine to host this dashboard
# Step 0
	Installation prerequisites
*  fully updated system `sudo apt update && sudo apt upgrade`
* `python3` on the system `sudo apt install python3`
* `pip` on the system `sudo apt install pip`
	
for the scripts you need the following python mondules : 
* `influxdb`
* `paramiko`
* `bs4`

install all of them using `pip install {module name}`
# Step 1 	
	Prepare the backend
* Install docker using any guide on the web 
* Pull and deploy the latest grafana image from [here](https://hub.docker.com/r/grafana/grafana). You can also install it bare metal instead of docker 
* Install influxDB server `sudo apt install influxdb` (will occupy 8086 port TCP)
* Install influxDB client so we can manage our databases easily `sudo apt install influxdb-client`
* Enable the influxdb service to start on boot and restart it 
   ```
   $ sudo systemctl enable influxdb
   $ sudo systemctl restart influxdb
   ```
Now using `systemctl status influxdb` you should see that service is running.

# Step 2
    Set up the database

* On terminal run:
```$ influx```
* Now you should run this influxDB query to create the database needed:
```> CREATE DATABASE modem```
* (Optional) Create a retention policy on database so it won't fill up the entire disk
  ```
  > CREATE RETENTION POLICY "16 weeks" ON "modem" DURATION 16w REPLICATION 1 DEFAULT
  ```
* Exit client using `exit`. Now database is ready.

# Step 3 
    Prepare the  bot / grafana enviroment 
* make a directory at root named eg `bot`   and place there the files `config.py` `router.py` &  `routerStatsInfluxDB.py`
*  Set the IP and login info correctly on the `config.py` file. 
* make a cron job with `crontab -e` , select nano then paste
    ```
    */10 * * * * nohup python3 /bot/routerStatsInfluxDB.py > /dev/null &
    ```
  This will update modem database every 10 minutes. Feel free to change the refresh rate.
* Login to grafana, add an influxdb dataset, set `url` to `http://localhost:8086`, and database name to `modem`.
* Import the dashboard .json file from this repository, and set its dataset to the one we created previously. 

Now we are ready to go. Test the bot by running `python3 /bot/routerStatsInfluxDB.py` , it should start populating the dashboard. Happy monitoring!
