# TidalTime
A simple script to:
1. scrape tidal prediction from BBC.co.uk
2. save to local db (sqlite)

A provided `locations.jsonl.gz` contains a table with available UK ports 
Alternatively you can goto `view-source:https://www.bbc.co.uk/weather/coast-and-sea/tide-tables`
and search for string 
```
type="application/json" data-data-id="tides"
```
and save the json string to a json file. The json object looks like this:
```json
{
  "version": "2.1.0",
  "countries": [
    {
      "name": "England",
      "id": null,
      "regions": [
        {
          "name": "East",
          "id": "1",
          "locations": [
            ...
          ]
        }]
        }]}

```
and then run `convert_locations.py` to conver it into `locations.jsonl.gz`

Change `config.cfg.template` to `config.cfg`.
To use slack notification please replace your slack webhook url
in `config.cfg`

Simply run `pip install`, and

```commandline
python collect_tides_info.py --help
```


Use in conjunction with cronjob
to monitor daily. e.g.:
```
0 4 * * * python /path/to/TidalTime/collect_tides_info.py -c config.cfg
```
