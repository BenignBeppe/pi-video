from flask import render_template

from app import app
from app.models import Video


@app.route("/history")
def history():
    videos = Video.query.all()
    return render_template("history.html", videos=videos)
