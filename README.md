## "TR-069" bot 
>Telemetry for xDSL networks 



## Table of contents
* [Project description ](#Project-description)
* [feature set ](#feature-set)
* [Progress ](#current-progress-of-the-project.)
* [Status](#Status)

## Project description 
Discord bot for remote management and statistics collection bot for discord, Technicolor modems and PfSense.


## feature set 
The target future set will be the following 
* Display on discord message xDSL statistics, 
* On request display graphs of these statistics
* Alert Network admin for any issues:
- high error rates, CGNAT  
- interface status changes

* How CRC /FEC errors are displayed on the RRD graph. 
A) standard, rolling graph, which shows the errors over time 
B) every 24h submit to the RRD the sum of the days’ worth of errors, 
That shows the points in time that peaked in errors. 

* Interact with the modem to re sync the line 


## Current progress of the project. 
* PfSense fauxapi & Python works 
* Parsing stats from TG789v V3 via ssh works 
* Discord messaging works via `NextCord`

TBD:
* VDSL uptime messages
* Alerts: CRC alerts (lots in a small time), DeSync, ReSync.
* onRequest: WAN_IP, Uptime 
* Alarms on high error counts
* CMD for restarting modem sync
* Displaying the RRD graphs, On discord
* Finalize The grafana Dashboard.

## Status
Project is: _in progress_

WORKING:

* Parsing of data (SSH) 
* Saving of Data (RRD)
* onRequest: VDSL_Stats, CRC/FEC_Counts,
* Alarm on Sync/Desync events
* CMD: Modem reboot with the `reboot` command. 

NOT WORKING: 
* RRD graphs scaling 
