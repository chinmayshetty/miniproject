from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import qrcode
import io
import base64
import json
import os
from datetime import datetime
import secrets

app = Flask(__name__)
CORS(app)

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "canteen2025"
ADMIN_PASSCODE = "12345"

# File paths
MENU_FILE = "menu_items.json"
ORDERS_FILE = "orders.json"

# Initialize files if they don't exist
def init_files():
    if not os.path.exists(MENU_FILE):
        default_menu = [
            {
                "id": 1,
                "name": "Masala Dosa",
                "price": 60,
                "category": "South Indian",
                "image": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=400"
            },
            {
                "id": 2,
                "name": "Paneer Butter Masala",
                "price": 120,
                "category": "North Indian",
                "image": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=400"
            },
            {
                "id": 3,
                "name": "Veg Biryani",
                "price": 100,
                "category": "Rice",
                "image": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=400"
            },
            {
                "id": 4,
                "name": "Chole Bhature",
                "price": 80,
                "category": "North Indian",
                "image": "https://images.unsplash.com/photo-1626132647523-66f5bf380027?w=400"
            },
            {
                "id": 5,
                "name": "Idli Sambar",
                "price": 40,
                "category": "South Indian",
                "image": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=400"
            },
            {
                "id": 6,
                "name": "Veg Sandwich",
                "price": 50,
                "category": "Snacks",
                "image": "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=400"
            }
        ]
        with open(MENU_FILE, 'w') as f:
            json.dump(default_menu, f, indent=2)
    
    if not os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'w') as f:
            json.dump([], f)

init_files()

@app.route('/api/auth', methods=['POST'])
def authenticate():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    passcode = data.get('passcode')
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD and passcode == ADMIN_PASSCODE:
        return jsonify({"success": True, "message": "Authentication successful"})
    else:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route('/api/menu', methods=['GET'])
def get_menu():
    with open(MENU_FILE, 'r') as f:
        menu = json.load(f)
    return jsonify(menu)

@app.route('/api/menu', methods=['POST'])
def add_menu_item():
    data = request.json
    with open(MENU_FILE, 'r') as f:
        menu = json.load(f)
    
    new_id = max([item['id'] for item in menu]) + 1 if menu else 1
    new_item = {
        "id": new_id,
        "name": data['name'],
        "price": float(data['price']),
        "category": data['category'],
        "image": data['image']
    }
    menu.append(new_item)
    
    with open(MENU_FILE, 'w') as f:
        json.dump(menu, f, indent=2)
    
    return jsonify({"success": True, "item": new_item})

@app.route('/api/menu/<int:item_id>', methods=['DELETE'])
def delete_menu_item(item_id):
    with open(MENU_FILE, 'r') as f:
        menu = json.load(f)
    
    menu = [item for item in menu if item['id'] != item_id]
    
    with open(MENU_FILE, 'w') as f:
        json.dump(menu, f, indent=2)
    
    return jsonify({"success": True})

@app.route('/api/generate-qr', methods=['POST'])
def generate_qr():
    data = request.json
    order_id = secrets.token_hex(8)
    
    order_data = {
        "order_id": order_id,
        "items": data['items'],
        "total": data['total'],
        "timestamp": datetime.now().isoformat()
    }
    
    # Save order
    with open(ORDERS_FILE, 'r') as f:
        orders = json.load(f)
    orders.append(order_data)
    with open(ORDERS_FILE, 'w') as f:
        json.dump(orders, f, indent=2)
    
    # Generate QR code
    qr_data = json.dumps({
        "order_id": order_id,
        "items": data['items'],
        "total": data['total']
    })
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return jsonify({
        "success": True,
        "qr_code": f"data:image/png;base64,{img_base64}",
        "order_id": order_id
    })

@app.route('/api/verify-qr', methods=['POST'])
def verify_qr():
    data = request.json
    qr_data = json.loads(data['qr_data'])
    
    with open(ORDERS_FILE, 'r') as f:
        orders = json.load(f)
    
    order = next((o for o in orders if o['order_id'] == qr_data['order_id']), None)
    
    if order:
        return jsonify({"success": True, "order": order})
    else:
        return jsonify({"success": False, "message": "Order not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)