# TidalTime
A simple script to:
1. scrape tidal prediction from BBC
2. save to local db (sqlite)
3. sent Slack notification. 

Use in conjunction with cronjob
to monitor daily. e.g.:
```
0 4 * * * /home/wei/miniconda3/bin/python /home/wei/TidalTime/tide_time.py -p 104 -a 9
5 4 * * * /home/wei/miniconda3/bin/python /home/wei/TidalTime/tide_time.py -p 103 -a 9
0 21 * * 2,4 /home/wei/miniconda3/bin/python /home/wei/TidalTime/notification.py
```

