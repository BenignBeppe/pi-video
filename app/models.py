from datetime import datetime
from datetime import timezone

from app import db


class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, default="")
    page_url = db.Column(db.Text, nullable=False, index=True, unique=True)
    video_url = db.Column(db.Text, default="")
    time = db.Column(db.Integer, default=0)
    last_played = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    def __init__(self, page_url):
        self.page_url = page_url

    def __repr__(self):
        return (
            f"Video({self.title}, {self.page_url}, {self.video_url}, "
            f"{self.time}, {self.last_played})"
        )
