# TidalTime
A simple script to:
1. scrape tidal prediction from BBC.co.uk
2. save to local db (sqlite)
3. sent Slack notification. 

A provided `locations.jsonl.gz` contains a table with available UK ports (full list below)

Simply run `pip install`, and
```commandline
python collect_tides_info.py --help
```


Use in conjunction with cronjob
to monitor daily. e.g.:
```
0 4 * * * python /path/to/TidalTime/collect_tides_info.py -c config.cfg
```
