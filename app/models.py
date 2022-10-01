from app import db


class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_url = db.Column(db.Text, nullable=False, index=True, unique=True)
    video_url = db.Column(db.Text)

    def __init__(self, page_url):
        self.page_url = page_url

    def __repr__(self):
        return f"Video({self.page_url}, {self.video_url})"
