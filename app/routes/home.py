from flask import jsonify
from . import api

@api.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to Flask API"})
