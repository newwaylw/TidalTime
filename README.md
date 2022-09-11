# TidalTime
A simple script to:
1. scrape tidal prediction from BBC
2. save to local db (sqlite)
3. sent Slack notification. 

locations.csv contains a list of available UK tidal ports
change `config.json.template` to `config.json`.
To use slack notification please replace your slack webhook url
in `config.json`

Use in conjunction with cronjob
to monitor daily. e.g.:
```
0 4 * * * /home/wei/miniconda3/bin/python /home/wei/TidalTime/tide_time.py -p 104 -p 103
0 21 * * 2,4 /home/wei/miniconda3/bin/python /home/wei/TidalTime/notification.py -c config.json -p 103 -p 104 -t 0.5
```
