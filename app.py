from flask import Flask, jsonify, render_template, request
import sqlite3
from pathlib import Path
from uuid import uuid4

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "duck_farm.db"

INITIAL_PRODUCTS = [
    (1, "Утиная грудка", 12.00, "Нежное мясо для запекания и жарки.", "duck-breast.jpg"),
    (2, "Утиные ножки", 9.00, "Отлично подходят для запекания в духовке.", "duck-legs.jpg"),
    (3, "Целая утка", 25.00, "Для праздничного стола и семейного ужина.", "whole-duck.jpg"),
]

FARM = {
    "name": "Duck Farm",
    "description": "Ферма по выращиванию уток"
}


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL CHECK(price >= 0),
                description TEXT NOT NULL DEFAULT '',
                image TEXT NOT NULL DEFAULT ''
            )
        """)
        # Migration for a database created by an earlier version of this project.
        product_columns = {
            row["name"] for row in db.execute("PRAGMA table_info(products)").fetchall()
        }
        if "image" not in product_columns:
            db.execute("ALTER TABLE products ADD COLUMN image TEXT NOT NULL DEFAULT ''")

        db.execute("""
            CREATE TABLE IF NOT EXISTS cart_items (
                cart_id TEXT NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                PRIMARY KEY (cart_id, product_id),
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        """)
        count = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count == 0:
            db.executemany(
                "INSERT INTO products (id, name, price, description, image) VALUES (?, ?, ?, ?, ?)",
                INITIAL_PRODUCTS
            )


def product_to_dict(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "price": round(float(row["price"]), 2),
        "currency": "USD",
        "description": row["description"],
        "image": row["image"]
    }


def get_cart_id():
    cart_id = request.headers.get("X-Cart-ID", "").strip()
    if not cart_id or len(cart_id) > 80:
        return None
    return cart_id


def get_cart_payload(db, cart_id):
    rows = db.execute("""
        SELECT p.id, p.name, p.price, p.description, p.image, ci.quantity
        FROM cart_items ci
        JOIN products p ON p.id = ci.product_id
        WHERE ci.cart_id = ?
        ORDER BY p.id
    """, (cart_id,)).fetchall()

    items = []
    total_items = 0
    total_price_cents = 0
    for row in rows:
        price_cents = round(float(row["price"]) * 100)
        subtotal_cents = price_cents * row["quantity"]
        total_items += row["quantity"]
        total_price_cents += subtotal_cents
        items.append({
            **product_to_dict(row),
            "quantity": row["quantity"],
            "subtotal": round(subtotal_cents / 100, 2)
        })

    return {
        "cart_id": cart_id,
        "items": items,
        "total_items": total_items,
        "total_price": round(total_price_cents / 100, 2),
        "currency": "USD"
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.get("/api")
def api_info():
    return jsonify({
        "name": "Duck Farm REST API",
        "currency": "USD",
        "endpoints": {
            "GET /api/products": "Get all products",
            "GET /api/products/<id>": "Get one product",
            "GET /api/farm": "Get farm information",
            "GET /api/cart": "Get cart (send X-Cart-ID header)",
            "POST /api/cart/items": "Add product to cart",
            "PATCH /api/cart/items/<product_id>": "Set cart item quantity",
            "DELETE /api/cart/items/<product_id>": "Remove item from cart",
            "DELETE /api/cart": "Clear cart"
        }
    })


@app.get("/api/products")
def get_products():
    with get_db() as db:
        rows = db.execute("SELECT * FROM products ORDER BY id").fetchall()
    return jsonify([product_to_dict(row) for row in rows]), 200


@app.get("/api/products/<int:product_id>")
def get_product(product_id):
    with get_db() as db:
        row = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if row is None:
        return jsonify({"error": "Товар не найден"}), 404
    return jsonify(product_to_dict(row)), 200


@app.get("/api/farm")
def get_farm():
    return jsonify(FARM), 200


@app.get("/api/cart")
def get_cart():
    cart_id = get_cart_id()
    if not cart_id:
        return jsonify({"error": "Передайте уникальный идентификатор корзины в заголовке X-Cart-ID"}), 400
    with get_db() as db:
        return jsonify(get_cart_payload(db, cart_id)), 200


@app.post("/api/cart/items")
def add_cart_item():
    cart_id = get_cart_id()
    if not cart_id:
        return jsonify({"error": "Передайте уникальный идентификатор корзины в заголовке X-Cart-ID"}), 400

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Ожидается JSON-объект"}), 400

    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)
    if isinstance(product_id, bool) or not isinstance(product_id, int) or product_id < 1:
        return jsonify({"error": "product_id должен быть положительным целым числом"}), 400
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1 or quantity > 99:
        return jsonify({"error": "quantity должен быть целым числом от 1 до 99"}), 400

    with get_db() as db:
        product = db.execute("SELECT id FROM products WHERE id = ?", (product_id,)).fetchone()
        if product is None:
            return jsonify({"error": "Товар не найден"}), 404

        current = db.execute(
            "SELECT quantity FROM cart_items WHERE cart_id = ? AND product_id = ?",
            (cart_id, product_id)
        ).fetchone()
        new_quantity = quantity + (current["quantity"] if current else 0)
        if new_quantity > 99:
            return jsonify({"error": "В корзине нельзя хранить больше 99 единиц одного товара"}), 400

        db.execute("""
            INSERT INTO cart_items (cart_id, product_id, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(cart_id, product_id)
            DO UPDATE SET quantity = excluded.quantity
        """, (cart_id, product_id, new_quantity))
        payload = get_cart_payload(db, cart_id)

    return jsonify(payload), 201


@app.patch("/api/cart/items/<int:product_id>")
def update_cart_item(product_id):
    cart_id = get_cart_id()
    if not cart_id:
        return jsonify({"error": "Передайте уникальный идентификатор корзины в заголовке X-Cart-ID"}), 400

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Ожидается JSON-объект"}), 400

    quantity = data.get("quantity")
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1 or quantity > 99:
        return jsonify({"error": "quantity должен быть целым числом от 1 до 99"}), 400

    with get_db() as db:
        existing = db.execute(
            "SELECT quantity FROM cart_items WHERE cart_id = ? AND product_id = ?",
            (cart_id, product_id)
        ).fetchone()
        if existing is None:
            return jsonify({"error": "Товара нет в корзине"}), 404
        db.execute(
            "UPDATE cart_items SET quantity = ? WHERE cart_id = ? AND product_id = ?",
            (quantity, cart_id, product_id)
        )
        payload = get_cart_payload(db, cart_id)

    return jsonify(payload), 200


@app.delete("/api/cart/items/<int:product_id>")
def remove_cart_item(product_id):
    cart_id = get_cart_id()
    if not cart_id:
        return jsonify({"error": "Передайте уникальный идентификатор корзины в заголовке X-Cart-ID"}), 400

    with get_db() as db:
        cursor = db.execute(
            "DELETE FROM cart_items WHERE cart_id = ? AND product_id = ?",
            (cart_id, product_id)
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "Товара нет в корзине"}), 404
        payload = get_cart_payload(db, cart_id)

    return jsonify(payload), 200


@app.delete("/api/cart")
def clear_cart():
    cart_id = get_cart_id()
    if not cart_id:
        return jsonify({"error": "Передайте уникальный идентификатор корзины в заголовке X-Cart-ID"}), 400

    with get_db() as db:
        db.execute("DELETE FROM cart_items WHERE cart_id = ?", (cart_id,))
        payload = get_cart_payload(db, cart_id)

    return jsonify(payload), 200


init_db()

if __name__ == "__main__":
    app.run(debug=True)
