# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(min=3, max=100)])
    description = StringField('Description', validators=[DataRequired(), Length(min=10, max=500)])
    price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    quantity = IntegerField('Quantity Available', validators=[DataRequired(), NumberRange(min=0)])
    image_url = StringField('Image URL', validators=[DataRequired(), Length(min=5, max=255)])
    submit = SubmitField('Add Product')
