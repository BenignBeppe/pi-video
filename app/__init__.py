import logging

from flask import Flask


app = Flask(__name__)

log_format = "%(asctime)s %(levelname)s %(message)s"
logging.basicConfig(format=log_format, level=logging.DEBUG)


from app import player # noqa E402
