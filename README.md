# Sales Order & Inventory Management System

A Flask and MySQL-based web application for managing customers, products, inventory, sales orders, and stock movements. Developed as part of the Savyant Systems Fresher/Trainee Technical Assignment.

## 1. Project Overview

The Sales Order & Inventory Management System helps businesses manage their sales and inventory operations through a centralized web application.

### Key Features

- User login and logout with hashed passwords.
- Admin and Sales User roles.
- Customer and product management.
- Inventory and stock adjustments.
- Stock movement history.
- Draft sales order creation.
- Order confirmation and cancellation.
- Automatic stock deduction and restoration.
- Order discount calculations.
- CSV product import with validation and duplicate prevention.
- Product search API.
- Sales and inventory reports.
- Standalone SQL reporting queries.

## 2. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web framework |
| MySQL 8+ | Relational database |
| SQLAlchemy | ORM and database operations |
| HTML, CSS, JavaScript | Frontend |
| Flask-Login | User authentication |
| Pytest | Automated testing |
| Git | Version control |

## 3. Project Structure

```text
Sales_Order_Inventory_Management/
│
├── app/
│   ├── routes/
│   │   ├── auth.py
│   │   ├── imports.py
│   │   ├── main.py
│   │   ├── master.py
│   │   ├── orders.py
│   │   └── reports.py
│   │
│   ├── templates/
│   ├── static/
│   ├── models.py
│   └── __init__.py
│
├── sample_data/
│   └── create_admin.py
│
├── tests/
│   ├── test_app.py
│   └── test_debugging.py
│
├── run.py
├── run_sql_queries.py
├── sql_queries.sql
├── API_DOCUMENTATION.md
├── requirements.txt
└── README.md
```

## 4. System Requirements

- Python 3.12 or later.
- MySQL Server 8 or later.
- Git.
- Visual Studio Code (recommended).

The project has been tested in a Python 3.14.6 virtual environment.

## 5. Installation and Setup

### Step 1: Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd Sales_Order_Inventory_Management
```

### Step 2: Create a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

### Step 3: Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### Step 4: Create the MySQL database

Execute the following SQL in MySQL:

```sql
CREATE DATABASE sales_inventory;
```

### Step 5: Configure environment variables

Copy `.env.example` to `.env`.

Update the database connection settings with your own MySQL username, password, and database name.

Do not commit your `.env` file or expose database credentials.

### Step 6: Create database tables

```powershell
python -c "from app import create_app, db; app=create_app(); app.app_context().push(); db.create_all(); print('Tables created')"
```

### Step 7: Create the Admin account

```powershell
python -m sample_data.create_admin
```

Follow the prompts to create your Admin account.

### Step 8: Run the application

```powershell
python run.py
```

Open the application:

http://127.0.0.1:5000/login

## 6. Database Design

The application uses six main database entities:

| Entity | Description |
|---|---|
| User | Stores user accounts and roles |
| Customer | Stores customer information |
| Product | Stores product details and stock |
| SalesOrder | Stores sales order information |
| SalesOrderItem | Stores individual order items |
| StockMovement | Records inventory changes |

Monetary fields use SQL DECIMAL and Python Decimal for accurate financial calculations.

Order items retain the product price at the time the order is created.

## 7. API Documentation

### GET /api/products

Retrieves active products.

Optional query parameter:

- `q`: Search products by name.

Example:

```text
GET http://127.0.0.1:5000/api/products?q=keyboard
```

Example response:

```json
[
  {
    "id": 1,
    "code": "PRD-001",
    "name": "Keyboard",
    "price": "1500.00",
    "stock": 18
  }
]
```

Authentication through a logged-in user session is required.

### POST /api/orders

The endpoint currently returns HTTP 501 Not Implemented. JSON order creation is a planned extension.

For now, create orders through the web application at `/orders/new`.

See `API_DOCUMENTATION.md` for additional details.

## 8. SQL Reporting Queries

The project includes five standalone SQL reporting queries:

1. Top three customers by confirmed order grand total.
2. Top three products by quantity sold.
3. Customers who have never placed an order.
4. Month-wise confirmed sales totals.
5. Products below a specified stock threshold.

Execute the verified queries using:

```powershell
python run_sql_queries.py
```

The current stock threshold in the script is 10.

## 9. Automated Testing

The project uses Pytest.

Run the complete test suite:

```powershell
python -m pytest tests -v
```

### Current Test Results

- Application tests: 3 passed.
- Debugging exercise tests: 7 passed.
- Total: 10 passed.

These tests cover home page access, login page access, invalid login handling, calculation validation, and invalid input handling.

## 10. CSV Product Import

The application supports CSV product imports.

Required CSV columns:

```text
product_code,product_name,category,price,stock_quantity,status
```

Validation includes:

- Required column checking.
- Blank product code detection.
- Duplicate product code prevention.
- Product name and category validation.
- Negative price and stock prevention.
- Product status validation.
- All-or-nothing import processing.

## 11. Current Limitations and Future Improvements

The following features remain to be completed or verified before final submission:

- Customer and product edit, deactivate, and safe-delete functionality.
- Admin interface for creating Sales User accounts.
- Additional ownership and role-permission tests.
- JSON-based order creation API.
- JSON order detail, confirmation, and cancellation endpoints.
- API pagination.
- Expanded automated tests covering all assignment scenarios.
- Additional report date-range and edge-case testing.
- CSRF protection and production configuration review.
- Final demo screenshots and a 5–8 minute demonstration video.

## 12. Security Considerations

- Passwords are stored using password hashing.
- Database credentials are configured through environment variables.
- Authenticated routes use Flask-Login.
- Database transactions are used for order and inventory operations.

Review the security configuration before production deployment.

## 13. Author

Developed as a technical assignment project for Savyant Systems.

---

**Project:** Sales Order & Inventory Management System  
**Backend:** Python Flask  
**Database:** MySQL  
**Testing:** Pytest
