from flask import Blueprint

log_analyzer = Blueprint('log_analyzer', __name__)

from . import views
