
import csv
from io import TextIOWrapper
from decimal import Decimal, InvalidOperation
from flask import Blueprint, request, redirect, url_for, flash, render_template
from flask_login import current_user
from app import db
from app.decorators import admin_required
from app.models import Product, StockMovement

imports_bp = Blueprint("imports", __name__)

@imports_bp.route("/import-products", methods=["GET", "POST"])
@admin_required
def import_products():

    if request.method == "POST":

        upload = request.files.get("file")

        if not upload or not upload.filename:
            flash("Choose a CSV file.", "error")
            return redirect(url_for("imports.import_products"))

        try:
            text_file = TextIOWrapper(
                upload.stream,
                encoding="utf-8-sig",
                newline=""
            )

            reader = csv.DictReader(text_file)

            required = {
                "product_code",
                "product_name",
                "category",
                "price",
                "stock_quantity",
                "status"
            }

            if not reader.fieldnames:
                flash("CSV file is empty or missing headers.", "error")
                return redirect(url_for("imports.import_products"))

            # Normalize CSV column names
            reader.fieldnames = [
                name.strip().lower() if name else ""
                for name in reader.fieldnames
            ]

            if not required.issubset(set(reader.fieldnames)):
                missing = required - set(reader.fieldnames)
                flash(
                    "Missing required columns: " + ", ".join(sorted(missing)),
                    "error"
                )
                return redirect(url_for("imports.import_products"))

            rows = []
            errors = []
            seen = set()

            for line, row in enumerate(reader, start=2):

                try:
                    # Normalize row values
                    row = {
                        key.strip().lower(): (value or "").strip()
                        for key, value in row.items()
                        if key is not None
                    }

                    code = row["product_code"]
                    name = row["product_name"]
                    category = row["category"]

                    price = Decimal(row["price"])
                    stock = int(row["stock_quantity"])
                    status = row["status"].capitalize()

                    if not code:
                        raise ValueError("Product code cannot be blank")

                    if code in seen or Product.query.filter_by(
                        product_code=code
                    ).first():
                        raise ValueError("Duplicate product code")

                    if not name:
                        raise ValueError("Product name cannot be blank")

                    if not category:
                        raise ValueError("Category cannot be blank")

                    if not price.is_finite() or price < 0:
                        raise ValueError("Invalid or negative price")

                    if stock < 0:
                        raise ValueError("Stock cannot be negative")

                    if status not in ("Active", "Inactive"):
                        raise ValueError(
                            "Status must be Active or Inactive"
                        )

                    seen.add(code)

                    rows.append(
                        Product(
                            product_code=code,
                            name=name,
                            category=category,
                            price=price,
                            stock_quantity=stock,
                            status=status
                        )
                    )

                except (ValueError, InvalidOperation, KeyError) as exc:
                    errors.append(f"Row {line}: {exc}")

            if not rows and not errors:
                errors.append("CSV contains no product records")

            # All-or-nothing import
            if errors:

                flash(
                    "Nothing imported. " + " | ".join(errors),
                    "error"
                )

            else:

                try:
                    for product in rows:
                        db.session.add(product)

                    db.session.flush()

                    for product in rows:
                        if product.stock_quantity > 0:
                            db.session.add(
                                StockMovement(
                                    product_id=product.id,
                                    movement_type="Opening Stock",
                                    quantity_change=product.stock_quantity,
                                    reason="CSV opening stock import",
                                    created_by=current_user.id
                                )
                            )

                    db.session.commit()

                    flash(
                        f"Successfully imported {len(rows)} products.",
                        "success"
                    )

                except Exception:
                    db.session.rollback()
                    flash(
                        "Import failed. No products were imported.",
                        "error"
                    )

        except (UnicodeDecodeError, csv.Error):
            flash("Invalid CSV file format.", "error")

        return redirect(url_for("imports.import_products"))

    return render_template("import_products.html")
