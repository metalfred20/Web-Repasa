from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Function to get a connection to the database
def get_db_connection():
    conn = sqlite3.connect('ecommerce.db')
    conn.row_factory = sqlite3.Row
    return conn

# Rutas

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# Route for the login page
@app.route('/login')
def login():
    return render_template('login.html')

# Route for a WordPress view
@app.route('/wordpress')
def wordpressview():
    return render_template('wordpress.html')

# Route to display a paginated list of products
@app.route('/products')
def product_list():
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 12

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve products for the current page
    cursor.execute('SELECT * FROM products LIMIT ?, ?', (start_idx, per_page))
    products_to_display = cursor.fetchall()

    # Calculate total number of products and pages
    total_products = cursor.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    total_pages = (total_products // per_page) + (1 if total_products % per_page > 0 else 0)

    # Close the database connection
    cursor.close()
    conn.close()

    # Render the template with the paginated product list
    return render_template(
        'product_list_paginated.html',
        products=products_to_display,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        cart_size=get_cart_size(),
        total_price=get_total_price()
    )

# Route to add a product to the shopping cart
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert the selected product into the shopping cart
    cursor.execute('INSERT INTO cart (product_id, quantity) VALUES (?, 1)', (product_id,))
    conn.commit()

    # Close the database connection
    cursor.close()
    conn.close()

    # Redirect back to the product list
    return redirect(url_for('product_list'))

# Route to view the shopping cart
@app.route('/view_cart')
def view_cart():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve information about products in the shopping cart
    cursor.execute('''
        SELECT p.id, p.name, p.price, c.quantity
        FROM products p
        JOIN cart c ON p.id = c.product_id
    ''')
    cart_data = cursor.fetchall()

    # Calculate the total price of items in the shopping cart
    total_price = sum(row[2] * row[3] for row in cart_data)

    # Close the database connection
    cursor.close()
    conn.close()

    # Render the template with the shopping cart information
    return render_template('cart.html', cart=cart_data, total_price=total_price)

# Route to remove a product from the shopping cart
@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Remove the selected product from the shopping cart
    cursor.execute('DELETE FROM cart WHERE product_id = ?', (product_id,))
    conn.commit()

    # Close the database connection
    cursor.close()
    conn.close()

    # Redirect back to the shopping cart view
    return redirect(url_for('view_cart'))

# Route to edit the quantity of a product in the shopping cart
@app.route('/edit_quantity/<int:product_id>', methods=['GET'])
def edit_quantity(product_id):
    new_quantity = int(request.args.get('quantity', 1))

    # Ensure the new quantity is greater than 0
    if new_quantity > 0:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Update the quantity of the selected product in the shopping cart
        cursor.execute('UPDATE cart SET quantity = ? WHERE product_id = ?', (new_quantity, product_id))
        conn.commit()

        # Close the database connection
        cursor.close()
        conn.close()

    # Redirect back to the shopping cart view
    return redirect(url_for('view_cart'))

# Function to get the size of the shopping cart
def get_cart_size():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve the count of items in the shopping cart
    cursor.execute('SELECT COUNT(*) FROM cart')
    cart_size = cursor.fetchone()[0]

    # Close the database connection
    cursor.close()
    conn.close()

    return cart_size

# Function to get the total price of items in the shopping cart
def get_total_price():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Calculate the total price of items in the shopping cart
    cursor.execute('''
        SELECT SUM(p.price * c.quantity)
        FROM products p
        JOIN cart c ON p.id = c.product_id
    ''')
    total_price = cursor.fetchone()[0]
    total_price = total_price if total_price is not None else 0.0

    # Close the database connection
    cursor.close()
    conn.close()

    return total_price

# Run the Flask application
if __name__ == '__main__':
    app.run(port=5050, debug=True)
