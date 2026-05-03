from flask import Blueprint

bp = Blueprint('main', __name__)

from ephergent_generator.main import routes