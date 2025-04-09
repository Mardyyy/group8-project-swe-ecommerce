from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from flask_migrate import Migrate

migrate = Migrate()
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile('config.py')

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from .routes import auth_routes, product_routes, cart_routes, admin_routes, home_routes
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(product_routes.bp)
    app.register_blueprint(cart_routes.bp)
    app.register_blueprint(admin_routes.bp)
    app.register_blueprint(home_routes.bp)
    
    return app
