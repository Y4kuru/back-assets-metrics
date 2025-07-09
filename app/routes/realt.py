from app.controllers.realt_controller import load_and_get_realt_rent_data
from . import api

@api.route("/realt/rent", methods=["GET"])
def get_rent_data():
    return load_and_get_realt_rent_data()
