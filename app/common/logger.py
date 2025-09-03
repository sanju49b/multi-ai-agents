import logging
import os 
#The os is used to store all the logs in the directory
from datetime import datetime

#Folder
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR,exist_ok=True)

#Day by day LOG Creation based on the date

LOG_FILE = os.path.join(LOGS_DIR, f"log_{datetime.now().strftime('%Y-%m-%d')}.log")

#configuring log

logging.basicConfig(
    filename=LOG_FILE,
    format= '%(asctime)s - %(levelname)s-%(message)s',
    level=logging.INFO,#gives the info,warning and error messages will get shown
)
#how log is create
#time -- level name (info,warning,error) -- Message

#The pain purpose of this is to pass logger in different files
def get_logger(name):
    logger =logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger


