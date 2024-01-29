from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__, static_url_path='/static')
app.secret_key = "asdfasdf"
# Function to get a connection to the database
def get_db_connection():
    conn = sqlite3.connect('ecommerce.db')
    conn.row_factory = sqlite3.Row
    if 'user_id' in session:
        user_id = session['user_id']

    return conn

def get_user_cart_data(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Recupera información sobre los productos en el carrito del usuario
    cursor.execute('''
        SELECT p.id, p.name, p.price, c.quantity
        FROM products p
        JOIN cart c ON p.id = c.product_id
        WHERE c.user_id = ?
    ''', (user_id,))

    cart_data = cursor.fetchall()

    cursor.close()
    conn.close()

    return cart_data

def clear_user_cart(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Elimina todos los productos del carrito del usuario
    cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
    conn.commit()

    cursor.close()
    conn.close()
###create order
@app.route('/generate_order', methods=['GET', 'POST'])
def generate_order():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get the user's cart information
        cart_data = get_user_cart_data(user_id)

        # Extract product_ids and quantities from the cart_data
        product_ids = [product['id'] for product in cart_data]
        quantities = [product['quantity'] for product in cart_data]

        # Insert a single order with all products from the cart
        cursor.execute('INSERT INTO orders (user_id, product_ids, quantities) VALUES (?, ?, ?)',
                       (user_id, ",".join(map(str, product_ids)), ",".join(map(str, quantities))))

        conn.commit()
        cursor.close()
        conn.close()

        # Clear the user's cart after creating the order
        clear_user_cart(user_id)

        order_generated = True  # Indicate that the order was successfully generated

        return render_template('create_order.html', cart=[], order_generated=order_generated)

    # Retrieve cart information for the current user
    user_id = session['user_id']
    cart_data = get_user_cart_data(user_id)

    return render_template('create_order.html', cart=cart_data)

# Modificación en la función view_orders en tu archivo de rutas
@app.route('/view_orders')
def view_orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve user's orders with product names from the orders and products tables
    cursor.execute('''
        SELECT o.id, p.name, o.product_ids, o.quantities
        FROM orders o
        JOIN products p ON ',' || o.product_ids || ',' LIKE '%,' || CAST(p.id AS TEXT) || ',%'
        WHERE o.user_id = ?
    ''', (user_id,))

    orders = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('view_orders.html', orders=orders)



###
# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = verify_credentials(username, password)

        if user:
            # Establecer la sesión para el usuario
            session['user_id'] = user['id']
            return redirect(url_for('product_list'))
    
    return render_template('login.html')

# Route to display a paginated list of products
@app.route('/products')
def product_list():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 8

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve products for the current page, including the img_url column
    cursor.execute('SELECT id, name, price, description, image_url FROM products LIMIT ?, ?', (start_idx, per_page))
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
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener el user_id de la sesión
    user_id = session.get('user_id')

    # Insertar el producto seleccionado en el carrito del usuario
    cursor.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, 1)', (user_id, product_id))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for('product_list'))


# Route to view the shopping cart
@app.route('/view_cart')
def view_cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()

    user_id = session.get('user_id')

    # Recuperar información sobre los productos en el carrito del usuario
    cursor.execute('''
        SELECT p.id, p.name, p.price, c.quantity
        FROM products p
        JOIN cart c ON p.id = c.product_id
        WHERE c.user_id = ?
    ''', (user_id,))

    cart_data = cursor.fetchall()

    total_price = sum(row[2] * row[3] for row in cart_data)

    cursor.close()
    conn.close()

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

@app.route('/search_products', methods=['GET'])
def search_products():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    query = request.args.get('query', '')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Realizar la búsqueda en los campos 'name' y 'description'
    cursor.execute('''
        SELECT * FROM products
        WHERE name LIKE ? OR description LIKE ?
    ''', ('%' + query + '%', '%' + query + '%'))

    search_results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('search_products.html', search_results=search_results)

#start mod for login

def verify_credentials(username, password):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Consultar credenciales desde la base de datos
    query = "SELECT * FROM users WHERE username=? AND password=?"
    cursor.execute(query, (username, password))
    user = cursor.fetchone()

    # Cerrar la conexión a la base de datos
    conn.close()

    # Verificar si se encontró un usuario y devolverlo como un diccionario
    if user:
        user_dict = {
            'id': user[0],
            'username': user[1],
            'password': user[2]
            # Agrega otros campos si es necesario
        }
        return user_dict
    else:
        return None

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
