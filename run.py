from flask import Flask, render_template

app = Flask(__name__)

# Dummy routes just for viewing templates
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/quotation')
def quotation():
    return render_template('quotation.html')

@app.route('/sales-order')
def sales_order():
    return render_template('sales_order.html')

@app.route('/purchase-order')
def purchase_order():
    return render_template('purchase_order.html')

@app.route('/material-receipt')
def material_receipt():
    return render_template('material_receipt.html')

@app.route('/inventory')
def inventory():
    return render_template('inventory.html')

@app.route('/production')
def production():
    return render_template('production.html')

@app.route('/login')
def login():
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
