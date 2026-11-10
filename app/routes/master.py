from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Customer, Product, SalesOrder, SalesOrderItem, StockMovement
from app.decorators import admin_required
from flask_login import login_required, current_user
from decimal import Decimal, InvalidOperation

master_bp = Blueprint("master", __name__)

@master_bp.route("/customers", methods=["GET", "POST"])
@admin_required
def customers():
    if request.method == "POST":
        customer = Customer(
            name=request.form.get("name", "").strip(),
            email=request.form.get("email", "").strip(),
            mobile=request.form.get("mobile", "").strip(),
            city=request.form.get("city", "").strip(),
            status=request.form.get("status", "Active")
        )
        if not customer.name:
            flash("Customer name is required.", "error")
        else:
            db.session.add(customer)
            db.session.commit()
            flash("Customer added.", "success")
            return redirect(url_for("master.customers"))
    term = request.args.get("q", "")
    query = Customer.query
    if term:
        query = query.filter(Customer.name.ilike(f"%{term}%"))
    return render_template("customers.html", customers=query.order_by(Customer.name).all())

@master_bp.route("/products", methods=["GET", "POST"])
@admin_required
def products():
    if request.method == "POST":
        try:
            price = Decimal(request.form.get("price", "0"))
            stock = int(request.form.get("stock_quantity", "0"))
            if price < 0 or stock < 0:
                raise ValueError
            product = Product(
                product_code=request.form["product_code"].strip(),
                name=request.form["name"].strip(),
                category=request.form["category"].strip(),
                price=price,
                stock_quantity=stock,
                status=request.form.get("status", "Active")
            )
            db.session.add(product)
            db.session.commit()
            flash("Product added.", "success")
            return redirect(url_for("master.products"))
        except (ValueError, InvalidOperation, KeyError):
            db.session.rollback()
            flash("Enter valid product details. Price and stock cannot be negative.", "error")
    term = request.args.get("q", "")
    query = Product.query
    if term:
        query = query.filter(Product.name.ilike(f"%{term}%") | Product.product_code.ilike(f"%{term}%"))
    return render_template("products.html", products=query.order_by(Product.name).all())

@master_bp.route("/stock-adjust", methods=["POST"])
@admin_required
def stock_adjust():
    try:
        product = db.session.get(Product, int(request.form["product_id"]))
        change = int(request.form["quantity_change"])
        reason = request.form["reason"].strip()
        if not product or not reason or change == 0 or product.stock_quantity + change < 0:
            raise ValueError
        product.stock_quantity += change
        db.session.add(StockMovement(product_id=product.id, movement_type="Adjustment",
            quantity_change=change, reason=reason, created_by=current_user.id))
        db.session.commit()
        flash("Stock adjusted.", "success")
    except (ValueError, KeyError):
        db.session.rollback()
        flash("Invalid adjustment. Stock cannot become negative and a reason is required.", "error")
    return redirect(url_for("master.products"))
