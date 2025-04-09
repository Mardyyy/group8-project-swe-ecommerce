from app import create_app, db
from app.models import User, Product
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Clear existing data
    db.drop_all()
    db.create_all()

    # Create admin user
    admin = User(
        username='admin',
        email='admin@example.com',
        password=generate_password_hash('admin123'),
        is_admin=True
    )

    # Create sample products
    product1 = Product(
        name='Wireless Mouse',
        description='Ergonomic wireless mouse with 2.4GHz connectivity',
        price=29.99,
        quantity=50,
        image_filename='mouse.jpg'
    )
    product2 = Product(
        name='Mechanical Keyboard',
        description='Backlit mechanical keyboard with blue switches',
        price=79.99,
        quantity=30,
        image_filename='keyboard.jpg'
    )
    product3 = Product(
        name='Noise Cancelling Headphones',
        description='Bluetooth headphones with active noise cancellation',
        price=129.99,
        quantity=20,
        image_filename='headphones.jpg'
    )

    # Add to session
    db.session.add(admin)
    db.session.add_all([product1, product2, product3])

    # Commit to DB
    db.session.commit()
    print("Database seeded successfully!")
