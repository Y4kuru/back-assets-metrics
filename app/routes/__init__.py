from flask import Blueprint

api = Blueprint('api', __name__)

# Import individual route files (which will register themselves on `api`)
from . import home, polls, stocks
