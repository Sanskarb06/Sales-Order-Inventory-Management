from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import select
from app import db
from app.models import Customer, Product, SalesOrder, SalesOrderItem, StockMovement

orders_bp = Blueprint("orders", __name__)
CENT = Decimal("0.01")

def money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)

def user_can_access(order):
    return current_user.role == "Admin" or order.created_by == current_user.id

@orders_bp.route("/orders/new", methods=["GET", "POST"])
@login_required
def new_order():
    customers = Customer.query.filter_by(status="Active").all()
    products = Product.query.filter_by(status="Active").all()
    if request.method == "POST":
        try:
            customer_id = int(request.form["customer_id"])
            discount = Decimal(request.form.get("discount_percentage", "0"))
            raw_ids = request.form.getlist("product_id[]")
            raw_qty = request.form.getlist("quantity[]")
            if not 0 <= discount <= 20 or not raw_ids or len(raw_ids) != len(raw_qty):
                raise ValueError("Check items and discount (0–20%).")
            if len(set(raw_ids)) != len(raw_ids):
                raise ValueError("Duplicate products are not allowed.")
            customer = db.session.get(Customer, customer_id)
            if not customer or customer.status != "Active":
                raise ValueError("Select an active customer.")
            order = SalesOrder(order_number="SO-" + uuid4().hex[:10].upper(),
                customer_id=customer_id, created_by=current_user.id,
                discount_percentage=discount)
            subtotal = Decimal("0.00")
            for pid, qty_text in zip(raw_ids, raw_qty):
                product = db.session.get(Product, int(pid))
                qty = int(qty_text)
                if not product or product.status != "Active" or qty <= 0:
                    raise ValueError("Choose active products and positive whole quantities.")
                rate = money(product.price)
                amount = money(rate * qty)
                subtotal += amount
                order.items.append(SalesOrderItem(product_id=product.id, quantity=qty,
                    rate=rate, amount=amount))
            order.subtotal = money(subtotal)
            order.discount_amount = money(order.subtotal * discount / Decimal("100"))
            order.grand_total = money(order.subtotal - order.discount_amount)
            db.session.add(order)
            db.session.commit()
            flash(f"Draft order {order.order_number} created.", "success")
            return redirect(url_for("orders.order_detail", order_id=order.id))
        except Exception as exc:
            db.session.rollback()
            flash(str(exc) or "Could not create order.", "error")
    return render_template("new_order.html", customers=customers, products=products)

@orders_bp.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    order = db.session.get(SalesOrder, order_id)
    if not order:
        abort(404)
    if not user_can_access(order):
        abort(403)
    return render_template("order_detail.html", order=order)

@orders_bp.route("/orders/<int:order_id>/confirm", methods=["POST"])
@login_required
def confirm_order(order_id):
    try:
        order = db.session.execute(
            select(SalesOrder).where(SalesOrder.id == order_id).with_for_update()
        ).scalar_one_or_none()
        if not order:
            abort(404)
        if not user_can_access(order):
            abort(403)
        if order.status != "Draft":
            raise ValueError("Only Draft orders can be confirmed.")
        # Lock product rows so concurrent confirmations cannot oversell stock.
        for item in order.items:
            product = db.session.execute(
                select(Product).where(Product.id == item.product_id).with_for_update()
            ).scalar_one()
            if product.stock_quantity < item.quantity:
                raise ValueError(f"Insufficient stock for {product.name}. No changes were made.")
        for item in order.items:
            product = db.session.get(Product, item.product_id)
            product.stock_quantity -= item.quantity
            db.session.add(StockMovement(product_id=product.id, movement_type="Sale",
                quantity_change=-item.quantity, order_id=order.id,
                reason=f"Order {order.order_number} confirmed", created_by=current_user.id))
        order.status = "Confirmed"
        db.session.commit()
        flash("Order confirmed and stock deducted.", "success")
    except Exception as exc:
        db.session.rollback()
        if getattr(exc, "code", None):
            raise
        flash(str(exc), "error")
    return redirect(url_for("orders.order_detail", order_id=order_id))

@orders_bp.route("/orders/<int:order_id>/cancel", methods=["POST"])
@login_required
def cancel_order(order_id):
    try:
        order = db.session.execute(
            select(SalesOrder).where(SalesOrder.id == order_id).with_for_update()
        ).scalar_one_or_none()
        if not order:
            abort(404)
        if not user_can_access(order):
            abort(403)
        if order.status == "Cancelled":
            raise ValueError("Order is already cancelled.")
        if order.status == "Confirmed":
            for item in order.items:
                product = db.session.execute(
                    select(Product).where(Product.id == item.product_id).with_for_update()
                ).scalar_one()
                product.stock_quantity += item.quantity
                db.session.add(StockMovement(product_id=product.id, movement_type="Return",
                    quantity_change=item.quantity, order_id=order.id,
                    reason=f"Order {order.order_number} cancelled", created_by=current_user.id))
        order.status = "Cancelled"
        db.session.commit()
        flash("Order cancelled.", "success")
    except Exception as exc:
        db.session.rollback()
        if getattr(exc, "code", None):
            raise
        flash(str(exc), "error")
    return redirect(url_for("orders.order_detail", order_id=order_id))

@orders_bp.route("/api/products")
@login_required
def api_products():
    term = request.args.get("q", "")
    query = Product.query.filter_by(status="Active")
    if term:
        query = query.filter(Product.name.ilike(f"%{term}%"))
    rows = query.order_by(Product.name).limit(50).all()
    return jsonify([{"id": p.id, "code": p.product_code, "name": p.name,
                     "price": str(p.price), "stock": p.stock_quantity} for p in rows])

@orders_bp.route("/api/orders", methods=["POST"])
@login_required
def api_create_order():
    return jsonify({"message": "Use the web order form for now. JSON order creation is a documented extension point."}), 501
