from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import Product
from app import db

bp = Blueprint('products', __name__, url_prefix='/products')

@bp.route('/index')
def index():
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', '')

    query = Product.query

    # Filter by search keyword
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%') | Product.description.ilike(f'%{search}%'))

    # Sort logic
    if sort_by == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'availability':
        query = query.order_by(Product.quantity.desc())

    products = query.all()
    
    return render_template('index.html', products=products, search=search, sort_by=sort_by)
