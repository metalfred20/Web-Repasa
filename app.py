# app.py

from flask import Flask, render_template, request

app = Flask(__name__)

# Productos que se obtendrán de Odoo
products = [
    {'id': i, 'name': f'Producto {i}', 'price': 10.0 + i} for i in range(1, 31)
]

# Rutas y funciones de la aplicación
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/products')
def product_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    products_to_display = products[start_idx:end_idx]

    total_products = len(products)
    total_pages = (total_products // per_page) + (1 if total_products % per_page > 0 else 0)

    return render_template(
        'product_list_paginated.html',
        products=products_to_display,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@app.route('/login')  # Agregar la ruta para 'login'
def login():
    return render_template('login.html')

if __name__ == '__main__':
    app.run(port=5050, debug=True)
