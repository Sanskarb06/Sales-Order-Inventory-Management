from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Customer, Product, SalesOrder

main_bp = Blueprint("main", __name__)

@main_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        customer_count=Customer.query.count(),
        product_count=Product.query.count(),
        order_count=SalesOrder.query.count(),
        user=current_user
    )
