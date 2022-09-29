import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pi-video.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

log_format = "%(asctime)s %(levelname)s %(message)s"
logging.basicConfig(format=log_format, level=logging.DEBUG)


from app import player # noqa E402
from app import models # noqa E402
