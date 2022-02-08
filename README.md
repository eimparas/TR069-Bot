## "TR-069" bot 
>Telemetry for xDSL networks 



## Table of contents
* [Project description](#Project-description)
* [feature set ](#feature-set)
* [Progress ](#current-progress-of-the-project.)
* [Status](#Status)


## Project description 
Discord bot for remote management and statistics collection bot for discord ,Technicolor modems and PfSense.


## feature set 
The target future set will be the following 
* Display on discord message xDSL statistics , 
* on request display graffs of these statistics
* Alert Network admin for any issues (high error rates , CGNAT , etc ) 
* and more...


## Current progress of the project. 
* PfSense fauxapi & Python works 
* parsing stats from TG789v V3 via ssh works 
* Discord messaging works via `NextCord`

TBD:
* Scaling rrd graph images 
* Finishing Tg789v V3 bot for displaying stats like CRC/FEC/ sync/Attainable on request, 
 
-alarms on high error counts, Sync/Desync events

-CMD for restaring modem sync.



## Status
Project is: _in progress_
