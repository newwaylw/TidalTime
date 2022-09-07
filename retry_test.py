import random
from tenacity import retry
from tenacity import stop_after_attempt


@retry(stop=stop_after_attempt(1))
def do_something_unreliable():
    if random.randint(0, 10) > 1:
        print("bad")
        raise IOError("Broken sauce, everything is hosed!!!111one")
    else:
        return "Awesome sauce!"


print(do_something_unreliable())