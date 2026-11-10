
from app import create_app, db
from sqlalchemy import text

app = create_app()

queries = {
    "Query 1 - Top 3 Customers": """
        SELECT
            c.id,
            c.name AS customer_name,
            COUNT(so.id) AS total_orders,
            SUM(so.grand_total) AS total_sales
        FROM customer c
        JOIN sales_order so
            ON c.id = so.customer_id
        WHERE so.status = 'Confirmed'
        GROUP BY c.id, c.name
        ORDER BY total_sales DESC
        LIMIT 3
    """,

    "Query 2 - Top 3 Products": """
        SELECT
            p.id,
            p.name AS product_name,
            SUM(soi.quantity) AS total_quantity_sold,
            SUM(soi.amount) AS gross_item_value
        FROM product p
        JOIN sales_order_item soi
            ON p.id = soi.product_id
        JOIN sales_order so
            ON soi.order_id = so.id
        WHERE so.status = 'Confirmed'
        GROUP BY p.id, p.name
        ORDER BY total_quantity_sold DESC
        LIMIT 3
    """,

    "Query 3 - Customers Without Orders": """
        SELECT
            c.id,
            c.name,
            c.email,
            c.mobile,
            c.city
        FROM customer c
        LEFT JOIN sales_order so
            ON c.id = so.customer_id
        WHERE so.id IS NULL
    """,

    "Query 4 - Month-wise Confirmed Sales": """
        SELECT
            YEAR(order_date) AS sales_year,
            MONTH(order_date) AS sales_month,
            MONTHNAME(order_date) AS month_name,
            COUNT(id) AS total_orders,
            SUM(grand_total) AS total_sales
        FROM sales_order
        WHERE status = 'Confirmed'
        GROUP BY
            YEAR(order_date),
            MONTH(order_date),
            MONTHNAME(order_date)
        ORDER BY sales_year, sales_month
    """,

    "Query 5 - Products Below Stock Threshold": """
        SELECT
            id,
            product_code,
            name,
            category,
            stock_quantity,
            price
        FROM product
        WHERE stock_quantity < :threshold
        ORDER BY stock_quantity ASC
    """
}

with app.app_context():

    for title, sql in queries.items():

        print("\n" + "=" * 65)
        print(title)
        print("=" * 65)

        parameters = {"threshold": 10} if "Query 5" in title else {}

        results = db.session.execute(
            text(sql),
            parameters
        ).fetchall()

        if results:
            for row in results:
                print(row)
        else:
            print("No records found.")

    print("\nAll five SQL queries executed successfully.")
