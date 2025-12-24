from flask import flash, redirect

from flaskpp import Module
from flaskpp.app.utils.auto_nav import autonav_route
from flaskpp.app.utils.translating import t
from flaskpp.utils import enabled
from .handling import your_endpoint


def init_routes(mod: Module):
    @mod.route("/")
    def index():
        return mod.render_template("index.html")

    @autonav_route(mod, "/vite-index", t("Vite Test"))
    def vite_index():
        if not enabled("FRONTEND_ENGINE"):
            flash("Vite is not enabled for this app.", "warning")
            return redirect("/")
        return mod.render_template("vite_index.html")

    @autonav_route(mod, "/your-endpoint", t("Your Endpoint"), methods=["GET", "POST"])
    def endpoint():
        return your_endpoint.handle_request()
