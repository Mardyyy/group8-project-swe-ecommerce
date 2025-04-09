from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user
from app.models import Product, CartItem, Order, OrderItem, DiscountCode
from app import db
from datetime import datetime

bp = Blueprint('cart', __name__, url_prefix='/cart')

@bp.route('/add/<int:product_id>')
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)

    existing_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()

    if existing_item:
        existing_item.quantity += 1
    else:
        new_item = CartItem(user_id=current_user.id, product_id=product.id, quantity=1)
        db.session.add(new_item)

    db.session.commit()
    flash(f"{product.name} added to cart.")
    return redirect(url_for('products.index'))

@bp.route('/')
@login_required
def view_cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()

    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    # tax = round(subtotal * 0.0825, 2)
    # total = subtotal + tax

    discount_code = request.args.get('discount', '')
    discount_amount = 0

    if discount_code:
        # Store the discount code in the session
        session['discount_code'] = discount_code

        code = DiscountCode.query.filter_by(code=discount_code, is_active=True).first()
        if code:
            discount_amount = round((subtotal * code.percentage / 100), 2)
            # total -= discount_amount
        else:
            flash("Invalid discount code")

    # Calculate tax after applying discount
    tax = round((subtotal - discount_amount) * 0.0825, 2)  # Tax should be calculated after discount
    total = round(subtotal - discount_amount + tax, 2)  # Final total (subtotal minus discount + tax)

    return render_template('cart.html', cart_items=cart_items, subtotal=subtotal, tax=tax,
                           total=total, discount=discount_amount, code=discount_code)

@bp.route('/place_order', methods=['POST'])
@login_required
def place_order():
    # Fetch the user's cart items
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()

    if not cart_items:
        flash("Your cart is empty.")
        return redirect(url_for('cart.view_cart'))

    # Calculate the subtotal (total of all items in the cart)
    subtotal = sum(item.product.price * item.quantity for item in cart_items)

    # Initialize discount amount
    discount_code = request.args.get('discount', '')
    discount_amount = 0

    # Get the discount code from the session (if any)
    discount_code = session.get('discount_code', '')
    if discount_code:
        # Check if discount code is valid
        code = DiscountCode.query.filter_by(code=discount_code, is_active=True).first()
        if code:
            # Calculate the discount amount (percentage off the subtotal)
            discount_amount = round((subtotal * code.percentage / 100), 2)
        else:
            flash("Invalid discount code", "danger")

    # Calculate tax after applying discount
    tax = round((subtotal - discount_amount) * 0.0825, 2)  # Tax should be calculated after discount
    total = round(subtotal - discount_amount + tax, 2)  # Final total (subtotal minus discount + tax)

    # Create the order and save to the database
    new_order = Order(
        user_id=current_user.id,
        total_amount=total,
        discount_code=discount_code if discount_amount > 0 else None,  # Store discount code if discount was applied
        discount_amount=discount_amount,  # Store the discount amount
        timestamp=datetime.utcnow(),
        status='Pending'
    )
    db.session.add(new_order)
    db.session.commit()  # Commit to generate order.id

    # Create order items and deduct inventory
    for item in cart_items:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.product.price,
            price=item.product.price * item.quantity  # Price per item
        )
        # Deduct inventory only if stock is available
        if item.product.quantity >= item.quantity:
            item.product.quantity -= item.quantity
            db.session.add(order_item)
        else:
            flash(f"Insufficient stock for {item.product.name}. Order could not be placed.", "danger")
            return redirect(url_for('cart.view_cart'))

    # Clear the cart
    for item in cart_items:
        db.session.delete(item)

    db.session.commit()  # Commit the changes
    flash("Order placed successfully!")

    # Clear the discount code from the session after placing the order
    session.pop('discount_code', None)
    
    return redirect(url_for('products.index'))


@bp.route('/remove/<int:item_id>')
@login_required
def remove_item(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
        flash("Item removed.")
    return redirect(url_for('cart.view_cart'))

@bp.route('/apply_discount', methods=['POST'])
@login_required
def apply_discount():
    discount_code = request.form.get('discount_code')
    if not discount_code:
        flash("Please enter a discount code.", "warning")
        return redirect(url_for('cart.view_cart'))

    # Check if the discount code is valid and active
    code = DiscountCode.query.filter_by(code=discount_code).first()
    if not code or not code.is_active:
        flash("Invalid or expired discount code.", "danger")
        return redirect(url_for('cart.view_cart'))

    # Calculate the discount
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for('cart.view_cart'))

    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    discount = (subtotal * code.percentage) / 100
    total = round(subtotal - discount, 2)

    # Save the applied discount to the user's session or cart (this is optional, depending on your flow)
    flash(f"Discount applied: -${discount:.2f}", "success")
    
    # You can store the discount code in the session or in the order when placing the order later
    return redirect(url_for('cart.view_cart', discount=discount, total=total))
