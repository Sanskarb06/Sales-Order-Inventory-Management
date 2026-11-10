-- 1. Top three customers by confirmed order grand total
SELECT c.id, c.name, SUM(o.grand_total) AS total_sales
FROM customer c JOIN sales_order o ON o.customer_id=c.id
WHERE o.status='Confirmed' GROUP BY c.id,c.name
ORDER BY total_sales DESC LIMIT 3;

-- 2. Top three products by quantity sold in confirmed orders
SELECT p.id,p.name,SUM(i.quantity) AS quantity_sold
FROM product p JOIN sales_order_item i ON i.product_id=p.id
JOIN sales_order o ON o.id=i.order_id
WHERE o.status='Confirmed' GROUP BY p.id,p.name
ORDER BY quantity_sold DESC LIMIT 3;

-- 3. Customers who have never placed any order
SELECT c.* FROM customer c
LEFT JOIN sales_order o ON o.customer_id=c.id WHERE o.id IS NULL;

-- 4. Month-wise confirmed sales totals
SELECT YEAR(order_date) AS sales_year, MONTH(order_date) AS sales_month,
SUM(grand_total) AS total_sales
FROM sales_order WHERE status='Confirmed'
GROUP BY YEAR(order_date),MONTH(order_date)
ORDER BY sales_year,sales_month;

-- 5. Products below a supplied stock threshold (replace 5 with your threshold)
SELECT * FROM product WHERE stock_quantity < 5;
