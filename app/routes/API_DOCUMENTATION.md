
# Sales Order and Inventory Management System
## API Documentation

### 1. Overview

This application provides API endpoints for retrieving active products and includes an extension point for JSON-based order creation.

Base URL:
http://127.0.0.1:5000

Authentication:
Users must be logged in to access the API endpoints.

---

### 2. Get Active Products

**Endpoint:** `/api/products`

**Method:** GET

**Description:** Retrieves active products. Supports searching products by name.

**Query Parameter:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| q | String | No | Search products by name |

**Example Request:**

GET /api/products

**Search Example:**

GET /api/products?q=keyboard

**Successful Response:**

Status Code: 200 OK

```json
[
  {
    "id": 1,
    "code": "PRD-001",
    "name": "Keyboard",
    "price": "1500.00",
    "stock": 20
  }
]
```

The response contains a maximum of 50 active products, ordered by product name.

---

### 3. Create Order Using JSON

**Endpoint:** `/api/orders`

**Method:** POST

**Description:** Reserved for future JSON-based order creation.

**Current Implementation:**

The endpoint does not currently create orders. It returns a not-implemented response.

**Response:**

Status Code: 501 Not Implemented

```json
{
  "message": "Use the web order form for now. JSON order creation is a documented extension point."
}
```

**Current Alternative:**

Use the web application order form at:

`/orders/new`

---

### 4. Authentication

Both API endpoints require an authenticated user session.

Unauthenticated users are redirected to the login page by Flask-Login.

Login page:

`/login`

---

### 5. Error and Status Codes

| Status Code | Meaning |
|---|---|
| 200 | Request successful |
| 302 | Redirect, including login redirect |
| 401 | Unauthorized, if configured by the application |
| 403 | Forbidden |
| 404 | Resource not found |
| 501 | API functionality not implemented |

---

### 6. Technology Stack

- Python
- Flask
- Flask-Login
- SQLAlchemy
- MySQL
- JSON

---

### 7. Testing

Run automated tests using:

```bash
python -m pytest tests -v
```
