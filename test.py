from tenacity import retry
from tenacity import stop_after_attempt, wait_exponential
import random

@retry(stop=stop_after_attempt(2))
def unstable_f():
  v  = random.random()
  print(v)
  if v < 0.5:
    return 0
  else:
    raise Exception("Something wrong!")


def run():
  try:
    a = unstable_f()
  except Exception as e:
    print(f"failed even though tried {unstable_f.retry.statistics['attempt_number']} times")

run()
