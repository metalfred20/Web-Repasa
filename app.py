from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Productos
products = [
    {'id': i, 'name': f'Producto {i}', 'price': 10.0 + i} for i in range(1, 101)
]

# Carrito de compras
cart = []

# Rutas
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/products')
def product_list():
    page = request.args.get('page', 1, type=int) #paginacion
    per_page = 12

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
        total_pages=total_pages,
        cart_size=len(cart),
        total_price=get_total_price()
    )

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = get_product_by_id(product_id)

    if product:
        cart.append(product)
        return redirect(url_for('product_list'))
    else:
        return 'Producto no encontrado', 404

@app.route('/cart')
def view_cart():
    return render_template('cart.html', cart=cart, total_price=get_total_price())

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    product = get_product_by_id(product_id)

    if product in cart:
        cart.remove(product)
    
    return redirect(url_for('view_cart'))

@app.route('/edit_quantity/<int:product_id>', methods=['GET'])
def edit_quantity(product_id):
    product = get_product_by_id(product_id)

    if product:
        new_quantity = int(request.args.get('quantity', 1))
        if new_quantity > 0:
            product['quantity'] = new_quantity

    return redirect(url_for('view_cart'))

def get_product_by_id(product_id):
    for product in products:
        if product['id'] == product_id:
            return product
    return None

def get_total_price():
    return sum(product['price'] * product.get('quantity', 1) for product in cart)

if __name__ == '__main__':
    app.run(port=5050, debug=True)
