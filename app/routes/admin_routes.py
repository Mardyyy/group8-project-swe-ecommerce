from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import Product, User, DiscountCode, Order, OrderItem
from app.utils.decorators import admin_required
from app.forms import ProductForm
from app import db


bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(func):
    """Simple check for admin. Adjust as needed based on your User model."""
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Access denied: Admins only.")
            return redirect(url_for('products.index'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return login_required(wrapper)


# Admin Dashboard
@bp.route('/dashboard')
@admin_required
def dashboard():
    users = User.query.all()
    products = Product.query.all()
    orders = Order.query.order_by(Order.timestamp.desc()).all()
    discounts = DiscountCode.query.all()
    return render_template('admin/dashboard.html', users=users, products=products, orders=orders, discounts=discounts)

# Example: Manage Products
@bp.route('/products')
@admin_required
def manage_products():
    products = Product.query.all()
    return render_template('admin/manage_products.html', products=products)

@bp.route('/add_product', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():

    form = ProductForm()

    if form.validate_on_submit():
        # Create a new product instance
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            quantity=form.quantity.data,
            image_url=form.image_url.data
        )

        # Add the product to the database
        db.session.add(product)
        db.session.commit()

        flash('Product added successfully!', 'success')
        return redirect(url_for('products.index'))  # Redirect to manage products page
    
    # Fetch all products to display
    products = Product.query.all()
    return render_template('admin/add_product.html', form=form, products=products)

@bp.route('/edit_product/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(id):

    product = Product.query.get(id)

    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('admin.manage_products'))

    form = ProductForm(obj=product)

    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.quantity = form.quantity.data
        product.image_url = form.image_url.data

        db.session.commit()

        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin.manage_products'))

    return render_template('admin/edit_product.html', form=form, product=product)

@bp.route('/delete_product/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_product(id):
    # if not current_user.is_admin:
    #     flash('You must be an admin to delete products.', 'danger')
    #     return redirect(url_for('products.index'))

    product = Product.query.get(id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('admin.manage_products'))

    db.session.delete(product)
    db.session.commit()

    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin.manage_products'))

# Example: Manage Users
@bp.route('/manage_users')
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

@bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)

    if request.method == 'POST':
        user.email = request.form['email']
        user.is_admin = 'is_admin' in request.form
        db.session.commit()
        flash('User updated successfully.')
        return redirect(url_for('admin.manage_users'))  # Make sure this route exists

    return render_template('admin/edit_user.html', user=user)

@bp.route('/users/<int:id>/delete', methods=['POST'])
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.')
    return redirect(url_for('admin.manage_users'))  # make sure this route exists


# Route to manage orders
@bp.route('/manage_orders')
@admin_required
def manage_orders():
    # Retrieve all orders sorted by date (most recent first)
    orders = Order.query.order_by(Order.timestamp.desc()).all()

    # Retrieve sort criteria from query params
    sort_by = request.args.get('sort_by', 'date')  # Default sort is by order date

    if not orders:  # If no orders exist
        flash('No orders found.', 'warning')
        return render_template('admin/manage_orders.html', orders=orders)

    if sort_by == 'date':
        orders = Order.query.order_by(Order.timestamp.desc()).all()  # Sort by order date (descending)
    elif sort_by == 'customer':
        orders = Order.query.join(User).order_by(User.username).all()  # Sort by customer (username)
    elif sort_by == 'amount':
        orders = Order.query.order_by(Order.total_amount.desc()).all()  # Sort by order total amount (descending)
    else:
        orders = Order.query.order_by(Order.timestamp.desc()).all()  # Default to order date sorting

    # Calculate the discounted total for each order and add it to the order's data
    for order in orders:
        # Get the order items for the current order
        order_items = OrderItem.query.filter_by(order_id=order.id).all()

        # Calculate the subtotal (total of all items before any discount)
        subtotal = sum(item.product.price * item.quantity for item in order_items)

        # Apply discount if present
        discount_amount = 0
        if order.discount_code:
            code = DiscountCode.query.filter_by(code=order.discount_code, is_active=True).first()
            if code:
                discount_amount = round(subtotal * code.percentage / 100, 2)

        # Calculate tax (based on the subtotal after discount)
        tax = round((subtotal - discount_amount) * 0.0825, 2)

        # Calculate the total price (after applying the discount and adding tax)
        total_price = round(subtotal - discount_amount + tax, 2)

        # Update the order's total amount with the calculated total price
        order.total_amount = total_price

    # Render the order management template with order data
    return render_template('admin/manage_orders.html', orders=orders, sort_by=sort_by)


# Route to view a specific order's details
@bp.route('/view_order/<int:id>')
@admin_required
def view_order(id):
    order = Order.query.get_or_404(id)
    order_items = OrderItem.query.filter_by(order_id=order.id).all()

    # Calculate the subtotal (total of all items before any discount)
    subtotal = sum(item.product.price * item.quantity for item in order_items)

    # Apply discount if present
    discount_amount = 0
    if order.discount_code:
        code = DiscountCode.query.filter_by(code=order.discount_code, is_active=True).first()
        if code:
            discount_amount = round(subtotal * code.percentage / 100, 2)

    # Calculate tax (based on the subtotal after discount)
    tax = round((subtotal - discount_amount) * 0.0825, 2)

    # Calculate total price (after applying the discount and adding tax)
    total_price = round(subtotal - discount_amount + tax, 2)

    return render_template('admin/view_order.html', order=order, order_items=order_items, 
                           subtotal=subtotal, discount_amount=discount_amount, tax=tax, total_price=total_price)


# Optionally, route to update the status of an order (e.g., "shipped", "delivered")
@bp.route('/orders/update_status/<int:id>', methods=['POST'])
@admin_required
def update_order_status(id):
    order = Order.query.get_or_404(id)
    new_status = request.form.get('status')
    
    # Update order status
    if new_status:
        order.status = new_status
        db.session.commit()
        flash(f"Order status updated to {new_status}.", 'success')
    else:
        flash("Invalid status.", 'danger')
    
    return redirect(url_for('admin.view_order', id=id))

# Manage discounts (view all discounts)
@bp.route('/discounts')
@login_required
def manage_discounts():
    discounts = DiscountCode.query.all()  # Get all discounts
    return render_template('admin/manage_discounts.html', discounts=discounts)

# Add a new discount
@bp.route('/discounts/add', methods=['GET', 'POST'])
@login_required
def add_discount():
    if request.method == 'POST':
        code = request.form['code']
        description = request.form['description']
        percentage = float(request.form['percentage'])
        is_active = 'is_active' in request.form

        # Create new discount
        new_discount = DiscountCode(code=code, description=description, percentage=percentage, is_active=is_active )
        db.session.add(new_discount)
        db.session.commit()

        flash("Discount added successfully!", "success")
        return redirect(url_for('admin.manage_discounts'))

    return render_template('admin/add_discount.html')

# Edit an existing discount
@bp.route('/discounts/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_discount(id):
    discount = DiscountCode.query.get_or_404(id)
    
    if request.method == 'POST':
        discount.code = request.form['code']
        discount.description = request.form['description']
        discount.percentage = float(request.form['percentage'])
        discount.is_active = 'active' in request.form

        db.session.commit()
        flash("Discount updated successfully!", "success")
        return redirect(url_for('admin.manage_discounts'))
    
    return render_template('admin/edit_discount.html', discount=discount)

# Delete a discount
@bp.route('/discounts/delete/<int:id>', methods=['POST'])
@login_required
def delete_discount(id):
    discount = DiscountCode.query.get_or_404(id)
    db.session.delete(discount)
    db.session.commit()
    
    flash("Discount deleted successfully!", "danger")
    return redirect(url_for('admin.manage_discounts'))

# You can add more routes:
# - Create/edit discounts
# - View order history
# - Sort/filter by customer/date/amount