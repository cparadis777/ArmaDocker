import logging
from logging.handlers import RotatingFileHandler
import sys
import datetime

def setup_logging():
    now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    server_log_file = f"arma_{now}_server_.log"
    manager_log_file=f"arma_{now}_manager.log"
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    server_file_handler = RotatingFileHandler(f"/logs/{server_log_file}", maxBytes=5*1024*1024, backupCount=2)
    server_file_handler.setFormatter(log_formatter)
    manager_file_handler = RotatingFileHandler(f"/logs/{manager_log_file}", maxBytes=5*1024*1024, backupCount=2)
    manager_file_handler.setFormatter(log_formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)

    logger = logging.getLogger("Manager")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(manager_file_handler)
    logger.addHandler(console_handler)

    server_logger = logging.getLogger(name="server")
    server_logger.setLevel(logging.DEBUG)
    server_logger.addHandler(server_file_handler)
    server_logger.addHandler(console_handler)
