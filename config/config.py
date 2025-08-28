import logging
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BASE_DIR = os.path.abspath(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), "..")
    )
    SOURCE_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
    SECRET_KEY = os.environ.get("SECRET_KEY", default="your_secret_key")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # Logger config
    LOG_LEVEL = logging.DEBUG
    LOG_DIR = os.path.join(SOURCE_DIR, "logs")
    LOG_FILE = os.path.join(LOG_DIR, "app.log")
    LOG_FORMAT = "('%(asctime)s - %(levelname)s - %(message)s')"
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
