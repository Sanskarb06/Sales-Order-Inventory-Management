from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import func
from app.models import Customer, SalesOrder, Product, SalesOrderItem, StockMovement
from app import db
reports_bp = Blueprint("reports", __name__)

@reports_bp.route("/")
@login_required
def index():
    start = request.args.get("start")
    end = request.args.get("end")
    query = db_query = Customer.query
    customers = query.order_by(Customer.name).all()
    summaries = []
    for customer in customers:
        orders = SalesOrder.query.filter_by(customer_id=customer.id, status="Confirmed")
        if start:
            orders = orders.filter(func.date(SalesOrder.order_date) >= start)
        if end:
            orders = orders.filter(func.date(SalesOrder.order_date) <= end)
        rows = orders.all()
        summaries.append({"customer": customer, "count": len(rows),
                          "total": sum((o.grand_total for o in rows), start=0)})
    product_sales = db.session.query(Product, func.coalesce(func.sum(SalesOrderItem.quantity), 0),
        func.coalesce(func.sum(SalesOrderItem.amount), 0)).join(
        SalesOrderItem, SalesOrderItem.product_id == Product.id).join(
        SalesOrder, SalesOrder.id == SalesOrderItem.order_id).filter(
        SalesOrder.status == "Confirmed").group_by(Product.id).all()
    low_stock = Product.query.filter(Product.stock_quantity < int(request.args.get("threshold", 5))).all()
    movements = StockMovement.query.order_by(StockMovement.created_at.desc()).limit(100).all()
    return render_template("reports.html", summaries=summaries,
        product_sales=product_sales, low_stock=low_stock, movements=movements)
