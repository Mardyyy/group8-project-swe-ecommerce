# app/routes/home_routes.py

from flask import Blueprint, redirect, url_for

bp = Blueprint('home', __name__)

@bp.route('/')
def homepage():
    return redirect(url_for('products.index'))  # This goes to /products/
