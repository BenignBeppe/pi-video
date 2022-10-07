from flask import render_template

from app import app
from app.models import Video


@app.route("/history")
def history():
    videos = Video.query.order_by(Video.last_played.desc()).all()
    return render_template("history.html", videos=videos)
