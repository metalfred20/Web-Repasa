from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Función para obtener una conexión a la base de datos
def get_db_connection():
    conn = sqlite3.connect('ecommerce.db')
    conn.row_factory = sqlite3.Row
    return conn

# productList = [
#     ("Kit de Clutch BMW", "Kit para motores E46", 1000.0, 50),
#     ("Kit Radiador BMW", "Kit para motores E46", 500.0, 70),
#     ("Kit Aceleracion BMW", "Kit para motores E46", 100.0, 40),
#     ("Kit de frenos BMW", "Kit generico, 1999-2010", 5000.0, 300),
#     ("Kit de Clutch VolksWagen", "Kit generico 1999-2006", 900.0, 76)
# ]


# def insertRows(productList): #funcion que recibe una lista con los datos, y  la inserta 
#     conn = sqlite3.connect("ecommerce.db")
#     cursor = conn.cursor()
#     instruccion = f"INSERT INTO products VALUES (?,?,?,?,?)" #en los interrogantes van los valores que vienen de la lista
#     cursor.executemany(instruccion, productList)
#     conn.commit()
#     conn.close()
    
# insertRows(productList)

# Rutas
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/wordpress')
def wordpressview():
    return render_template('wordpress.html')

@app.route('/products')
def product_list():
    page = request.args.get('page', 1, type=int)  # paginación
    per_page = 12

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM products LIMIT ?, ?', (start_idx, per_page))
    products_to_display = cursor.fetchall()

    total_products = cursor.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    total_pages = (total_products // per_page) + (1 if total_products % per_page > 0 else 0)

    cursor.close()
    conn.close()

    return render_template(
        'product_list_paginated.html',
        products=products_to_display,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        cart_size=get_cart_size(),
        total_price=get_total_price()
    )

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('INSERT INTO cart (product_id, quantity) VALUES (?, 1)', (product_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for('product_list'))

@app.route('/view_cart')
def view_cart():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.id, p.name, p.price, c.quantity
        FROM products p
        JOIN cart c ON p.id = c.product_id
    ''')
    cart_data = cursor.fetchall()

    total_price = sum(row[2] * row[3] for row in cart_data)

    cursor.close()
    conn.close()

    return render_template('cart.html', cart=cart_data, total_price=total_price)

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM cart WHERE product_id = ?', (product_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for('view_cart'))

@app.route('/edit_quantity/<int:product_id>', methods=['GET'])
def edit_quantity(product_id):
    new_quantity = int(request.args.get('quantity', 1))

    if new_quantity > 0:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('UPDATE cart SET quantity = ? WHERE product_id = ?', (new_quantity, product_id))
        conn.commit()

        cursor.close()
        conn.close()

    return redirect(url_for('view_cart'))



def get_cart_size():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM cart')
    cart_size = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return cart_size

def get_total_price():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT SUM(p.price * c.quantity)
        FROM products p
        JOIN cart c ON p.id = c.product_id
    ''')
    total_price = cursor.fetchone()[0]
    total_price = total_price if total_price is not None else 0.0

    cursor.close()
    conn.close()

    return total_price

if __name__ == '__main__':
    app.run(port=5050, debug=True)


