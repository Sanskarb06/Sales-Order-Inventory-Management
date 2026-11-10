
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, jsonify, abort
)
from flask_login import login_required, current_user
from sqlalchemy import select

from app import db
from app.models import (
    Customer, Product, SalesOrder,
    SalesOrderItem, StockMovement
)

orders_bp = Blueprint("orders", __name__)

CENT = Decimal("0.01")


def money(value):
    return Decimal(str(value)).quantize(
        CENT, rounding=ROUND_HALF_UP
    )


def parse_positive_integer(value, field_name):
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a whole number.")

    if isinstance(value, int):
        result = value
    elif isinstance(value, str) and value.strip().isdigit():
        result = int(value.strip())
    else:
        raise ValueError(f"{field_name} must be a whole number.")

    if result <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")

    return result


def user_can_access(order):
    return (
        current_user.role == "Admin"
        or order.created_by == current_user.id
    )


def order_to_json(order):
    return {
        "id": order.id,
        "order_number": order.order_number,
        "customer_id": order.customer_id,
        "order_date": order.order_date.isoformat(),
        "status": order.status,
        "discount_percentage": str(order.discount_percentage),
        "subtotal": str(order.subtotal),
        "discount_amount": str(order.discount_amount),
        "grand_total": str(order.grand_total),
        "items": [
            {
                "product_id": item.product_id,
                "product_name": item.product.name,
                "quantity": item.quantity,
                "rate": str(item.rate),
                "amount": str(item.amount)
            }
            for item in order.items
        ]
    }


# CREATE WEB ORDER

@orders_bp.route("/orders/new", methods=["GET", "POST"])
@login_required
def new_order():
    customers = Customer.query.filter_by(status="Active").all()
    products = Product.query.filter_by(status="Active").all()

    if request.method == "POST":
        try:
            customer_id = parse_positive_integer(
                request.form.get("customer_id"),
                "Customer ID"
            )

            discount = Decimal(
                request.form.get("discount_percentage", "0")
            )

            raw_ids = request.form.getlist("product_id[]")
            raw_qty = request.form.getlist("quantity[]")

            if (
                not discount.is_finite()
                or not 0 <= discount <= 20
                or not raw_ids
                or len(raw_ids) != len(raw_qty)
            ):
                raise ValueError("Check items and discount (0–20%).")

            if len(set(raw_ids)) != len(raw_ids):
                raise ValueError("Duplicate products are not allowed.")

            customer = db.session.get(Customer, customer_id)

            if not customer or customer.status != "Active":
                raise ValueError("Select an active customer.")

            order = SalesOrder(
                order_number="SO-" + uuid4().hex[:10].upper(),
                customer_id=customer_id,
                created_by=current_user.id,
                discount_percentage=discount
            )

            subtotal = Decimal("0.00")

            for pid, qty_text in zip(raw_ids, raw_qty):
                product_id = parse_positive_integer(pid, "Product ID")
                qty = parse_positive_integer(qty_text, "Quantity")

                product = db.session.get(Product, product_id)

                if not product or product.status != "Active":
                    raise ValueError("Choose an active product.")

                rate = money(product.price)
                amount = money(rate * qty)
                subtotal += amount

                order.items.append(
                    SalesOrderItem(
                        product_id=product.id,
                        quantity=qty,
                        rate=rate,
                        amount=amount
                    )
                )

            order.subtotal = money(subtotal)
            order.discount_amount = money(
                order.subtotal * discount / Decimal("100")
            )
            order.grand_total = money(
                order.subtotal - order.discount_amount
            )

            db.session.add(order)
            db.session.commit()

            flash(
                f"Draft order {order.order_number} created.",
                "success"
            )

            return redirect(
                url_for("orders.order_detail", order_id=order.id)
            )

        except Exception as exc:
            db.session.rollback()
            flash(str(exc) or "Could not create order.", "error")

    return render_template(
        "new_order.html",
        customers=customers,
        products=products
    )


# VIEW WEB ORDER

@orders_bp.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    order = db.session.get(SalesOrder, order_id)

    if not order:
        abort(404)

    if not user_can_access(order):
        abort(403)

    return render_template(
        "order_detail.html",
        order=order
    )


# CONFIRM ORDER

@orders_bp.route("/orders/<int:order_id>/confirm", methods=["POST"])
@login_required
def confirm_order(order_id):
    try:
        order = db.session.execute(
            select(SalesOrder)
            .where(SalesOrder.id == order_id)
            .with_for_update()
        ).scalar_one_or_none()

        if not order:
            abort(404)

        if not user_can_access(order):
            abort(403)

        if order.status != "Draft":
            raise ValueError("Only Draft orders can be confirmed.")

        for item in order.items:
            product = db.session.execute(
                select(Product)
                .where(Product.id == item.product_id)
                .with_for_update()
            ).scalar_one()

            if product.stock_quantity < item.quantity:
                raise ValueError(
                    f"Insufficient stock for {product.name}. "
                    "No changes were made."
                )

        for item in order.items:
            product = db.session.get(Product, item.product_id)
            product.stock_quantity -= item.quantity

            db.session.add(
                StockMovement(
                    product_id=product.id,
                    movement_type="Sale",
                    quantity_change=-item.quantity,
                    order_id=order.id,
                    reason=f"Order {order.order_number} confirmed",
                    created_by=current_user.id
                )
            )

        order.status = "Confirmed"
        db.session.commit()

        if request.is_json:
            return jsonify({
                "message": "Order confirmed successfully.",
                "order": order_to_json(order)
            }), 200

        flash("Order confirmed and stock deducted.", "success")

    except Exception as exc:
        db.session.rollback()

        if getattr(exc, "code", None):
            raise

        if request.is_json:
            return jsonify({"error": str(exc)}), 400

        flash(str(exc), "error")

    return redirect(
        url_for("orders.order_detail", order_id=order_id)
    )


# CANCEL ORDER

@orders_bp.route("/orders/<int:order_id>/cancel", methods=["POST"])
@login_required
def cancel_order(order_id):
    try:
        order = db.session.execute(
            select(SalesOrder)
            .where(SalesOrder.id == order_id)
            .with_for_update()
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
                    select(Product)
                    .where(Product.id == item.product_id)
                    .with_for_update()
                ).scalar_one()

                product.stock_quantity += item.quantity

                db.session.add(
                    StockMovement(
                        product_id=product.id,
                        movement_type="Return",
                        quantity_change=item.quantity,
                        order_id=order.id,
                        reason=f"Order {order.order_number} cancelled",
                        created_by=current_user.id
                    )
                )

        order.status = "Cancelled"
        db.session.commit()

        if request.is_json:
            return jsonify({
                "message": "Order cancelled successfully.",
                "order": order_to_json(order)
            }), 200

        flash("Order cancelled.", "success")

    except Exception as exc:
        db.session.rollback()

        if getattr(exc, "code", None):
            raise

        if request.is_json:
            return jsonify({"error": str(exc)}), 400

        flash(str(exc), "error")

    return redirect(
        url_for("orders.order_detail", order_id=order_id)
    )


# API: GET PRODUCTS WITH PAGINATION

@orders_bp.route("/api/products", methods=["GET"])
@login_required
def api_products():
    term = request.args.get("q", "")
    page = request.args.get("page", "1")
    per_page = request.args.get("per_page", "20")

    try:
        page = int(page)
        per_page = int(per_page)

        if page < 1 or not 1 <= per_page <= 100:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            "error": "Invalid pagination parameters."
        }), 400

    query = Product.query.filter_by(status="Active")

    if term:
        query = query.filter(Product.name.ilike(f"%{term}%"))

    pagination = query.order_by(Product.name).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    return jsonify({
        "products": [
            {
                "id": p.id,
                "code": p.product_code,
                "name": p.name,
                "price": str(p.price),
                "stock": p.stock_quantity
            }
            for p in pagination.items
        ],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages
        }
    }), 200


# API: CREATE ORDER

@orders_bp.route("/api/orders", methods=["POST"])
@login_required
def api_create_order():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must contain valid JSON."
        }), 400

    try:
        customer_id = parse_positive_integer(
            data.get("customer_id"),
            "Customer ID"
        )

        discount = Decimal(
            str(data.get("discount_percentage", 0))
        )

        items = data.get("items")

        if not isinstance(items, list) or not items:
            raise ValueError("At least one order item is required.")

        if (
            not discount.is_finite()
            or not Decimal("0") <= discount <= Decimal("20")
        ):
            raise ValueError("Discount must be between 0 and 20.")

        customer = db.session.get(Customer, customer_id)

        if not customer or customer.status != "Active":
            raise ValueError("Select an active customer.")

        order = SalesOrder(
            order_number="SO-" + uuid4().hex[:10].upper(),
            customer_id=customer_id,
            created_by=current_user.id,
            discount_percentage=discount
        )

        subtotal = Decimal("0.00")
        used_products = set()

        for item in items:
            if not isinstance(item, dict):
                raise ValueError("Each item must be a JSON object.")

            product_id = parse_positive_integer(
                item.get("product_id"),
                "Product ID"
            )

            quantity = parse_positive_integer(
                item.get("quantity"),
                "Quantity"
            )

            if product_id in used_products:
                raise ValueError("Duplicate products are not allowed.")

            used_products.add(product_id)

            product = db.session.get(Product, product_id)

            if not product or product.status != "Active":
                raise ValueError(
                    f"Product {product_id} is not available."
                )

            rate = money(product.price)
            amount = money(rate * quantity)
            subtotal += amount

            order.items.append(
                SalesOrderItem(
                    product_id=product.id,
                    quantity=quantity,
                    rate=rate,
                    amount=amount
                )
            )

        order.subtotal = money(subtotal)
        order.discount_amount = money(
            order.subtotal * discount / Decimal("100")
        )
        order.grand_total = money(
            order.subtotal - order.discount_amount
        )

        db.session.add(order)
        db.session.commit()

        return jsonify({
            "message": "Order created successfully.",
            "order": order_to_json(order)
        }), 201

    except (ValueError, TypeError, ArithmeticError) as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400

    except Exception:
        db.session.rollback()
        return jsonify({
            "error": "Unable to create order."
        }), 500


# API: GET SINGLE ORDER

@orders_bp.route("/api/orders/<int:order_id>", methods=["GET"])
@login_required
def api_get_order(order_id):
    order = db.session.get(SalesOrder, order_id)

    if not order:
        return jsonify({"error": "Order not found."}), 404

    if not user_can_access(order):
        return jsonify({
            "error": "You do not have permission to access this order."
        }), 403

    return jsonify({
        "order": order_to_json(order)
    }), 200


# API: GET ALL ORDERS WITH PAGINATION

@orders_bp.route("/api/orders", methods=["GET"])
@login_required
def api_get_orders():
    page = request.args.get("page", "1")
    per_page = request.args.get("per_page", "20")

    try:
        page = int(page)
        per_page = int(per_page)

        if page < 1 or not 1 <= per_page <= 100:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            "error": "Invalid pagination parameters."
        }), 400

    query = SalesOrder.query

    if current_user.role != "Admin":
        query = query.filter_by(created_by=current_user.id)

    pagination = query.order_by(
        SalesOrder.order_date.desc()
    ).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    return jsonify({
        "orders": [
            order_to_json(order)
            for order in pagination.items
        ],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages
        }
    }), 200
