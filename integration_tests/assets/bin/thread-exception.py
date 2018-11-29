import logging
import time
import threading

from xivo import xivo_logging

xivo_logging.setup_logging('/dev/null')

def failure():
    raise RuntimeError('If you see this, then the exception is logged!')

threading.Thread(target=failure).start()

while True:
    time.sleep(1)
