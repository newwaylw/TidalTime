import requests
import logging
import time


def send_msg(url: str, message, retry: int = 1):
    sent = False
    cnt = 0

    while not sent:
        r = requests.post(url, json={"text": message})
        cnt += 1
        if not (r.status_code == 200 and r.reason == "OK"):
            logging.debug(f"HTTP POST failed: {r.status_code} {r.reason}")
            if cnt > retry:
                logging.debug(f"failed {cnt} times, quitting")
                break
            time.sleep(min(300, 2**cnt))
        else:
            logging.debug(f"HTTP POST successful: {r.status_code} {r.reason}")
            sent = True