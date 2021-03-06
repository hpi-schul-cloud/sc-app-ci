import logging
import time
from pathlib import Path


def initLogging():
    '''
    Initializes the logger.
    '''
    logdir = './log'
    Path(logdir).mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    applicationName = 'sc-app-deploy'
    logFilename = '%s/%s_%s.log' % (logdir, timestamp, applicationName)
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s", "%Y-%m-%d %H:%M:%S")

    # The logger
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)
    
    # File handler
    fileHandler = logging.FileHandler(logFilename)
    fileHandler.setFormatter(logFormatter)
    fileHandler.setLevel(logging.DEBUG)
    rootLogger.addHandler(fileHandler)

    # Console handler
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    consoleHandler.setLevel(logging.INFO)
    rootLogger.addHandler(consoleHandler)
    
    logging.debug('Logging initialized')
