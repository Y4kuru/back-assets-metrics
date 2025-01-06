from flask import Blueprint, jsonify

api = Blueprint('api', __name__)

@api.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to Flask API"})
