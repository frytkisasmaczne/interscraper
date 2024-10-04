from flask import Flask, render_template, request
from sources import ic
from requests_html import HTMLSession

app = Flask(__name__)

session = HTMLSession()


@app.route("/")
def index():
    return render_template("index.html", title="bajojajo", stations=ic.stationsList(session))


@app.route("/search")
def search():
    return render_template("search.html", title="majomajo", results=ic.getWholeMonth(session, request.args.get("from"), request.args.get("to")))


@app.route("/debug/stations")
def stations():
    return ic.stationsJson(session)
