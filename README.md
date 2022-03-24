## "TR-069" bot 
>Telemetry for xDSL networks 



## Table of contents
* [Project description ](#Project-description)
* [Connection Diagram ](#PConnection-Diagram)
* [feature set ](#feature-set)
* [Progress ](#current-progress-of-the-project.)
* [Status](#Status)

## Project description 
Discord bot for remote management and statistics collection bot for discord, Technicolor modems and PfSense. 
* The idea behind the `modemBot` bot is to have an eye on line itself, Get notified if the line goes down, gets synced back up, its Stats, Its errors while you are away from the modem . This is accomplished by having a 2nd way to get to the internet, for me it was a simple ADSL line used only as a simple phone line that happened to carry internet. A 4g cellular connection for example is suitable.
* `pfsenseBot`s main duty is to inform about the wan IP. 
* Discord messaging works via `NextCord`

## Connection Diagram

_TO_BE_ADDED_

## Feature set 
> ModemBot: 
* Display on discord message xDSL statistics 
* On request display graphs of these statistics (replaced with grafana)
* Alert Network admin for any issues like (high error rates, Desync events etc)

Commands: 
* Interact with the modem to re sync the line 
* Interact with the modem to trigger a reboot

> PfsenseBot: 
- Allert the Network admin for CGNAT  
- inform Network admin for the DHCP wan Address in case the DDNS fails. 
- interface status changes (if PPP had Dropped and returned, this will ping the admin)
- Display data on Grafana

## Current progress of the project. 
* ModemBot deployed on final setup and long-term testing started 
* Grafana dashboard has to be finalized 
* PfsenseBot has to be deployed on a docker container. 

TBD:
* Alerts: CRC alerts (lots in a small time), Desync, Resync.
* On Request: WAN_IP, Uptime 
* CMD for restarting modem sync
* Finalize The grafana Dashboard.

## Status
Project is: _in progress_

# WORKING:

> For ModemBot: 

* Parsing of data (SSH) 
* Saving of Data (RRD)
* On Request: VDSL_Stats, CRC/FEC_Counts,
* Alarm on Sync/Desync events
* CMD: Modem reboot with the `reboot` command. 

> For PfsenseBot: 
* Wan interface Ip change alerts 
* CGNAT alerts (when the isp plays naughty)
* Interface Stats (RTT, Packet loss, etc)



## Screenshots: 

* Grafana Dashboard: 
 ![Grafana](https://github.com/finos2/TR069-Bot/blob/main/IMG/DashBoard.png?raw=true)
 
 * Status Discord Message: 
 
 ![Status](https://github.com/finos2/TR069-Bot/blob/main/IMG/DiscordStatus.png?raw=true)
