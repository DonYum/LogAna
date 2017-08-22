from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_pagedown import PageDown
from celery import Celery
from config import config, Config

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
pagedown = PageDown()
# Create the Flask-Celery-Helper's instance
celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    db.app = app
    login_manager.init_app(app)
    pagedown.init_app(app)
    # Init the Flask-Celery-Helper via app object
    # Register the celery object into app object
    celery.conf.update(app.config)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .log_analyzer import log_analyzer as log_analyzer_blueprint
    app.register_blueprint(log_analyzer_blueprint, url_prefix='/log_analyzer')

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app
