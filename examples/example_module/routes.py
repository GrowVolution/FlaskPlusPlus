from flask import Blueprint

from .handling import your_endpoint
from .utils import render_template
from flaskpp.app.utils.auto_nav import autonav_route
from flaskpp.app.utils.translating import t


def init_routes(bp: Blueprint):
    @bp.route("/")
    def index():
        return render_template("index.html")

    @autonav_route(bp, "/your-endpoint", t("Your Endpoint"), methods=["GET", "POST"])
    def endpoint():
        return your_endpoint.handle_request()
