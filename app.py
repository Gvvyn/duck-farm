
from flask import Flask, jsonify, request

app = Flask(__name__)

# Пример каталога товаров
products = [
    {
        "id": 1,
        "name": "Утиная грудка",
        "price": 1200,
        "description": "Филе утки"
    },
    {
        "id": 2,
        "name": "Утиные ножки",
        "price": 900,
        "description": "Ножки утки"
    },
    {
        "id": 3,
        "name": "Целая утка",
        "price": 2500,
        "description": "Целая тушка утки"
    }
]

farm = {
    "name": "Duck Farm",
    "description": "Ферма по выращиванию уток"
}


# Главная страница API
@app.route("/")
def home():
    return jsonify({
        "message": "Duck Farm API",
        "endpoints": [
            "GET /api/products",
            "GET /api/products/<id>",
            "POST /api/products",
            "PUT /api/products/<id>",
            "DELETE /api/products/<id>",
            "GET /api/farm"
        ]
    })


# Получение всех товаров
@app.route("/api/products", methods=["GET"])
def get_products():
    return jsonify(products), 200


# Получение одного товара
@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = next(
        (p for p in products if p["id"] == product_id),
        None
    )

    if product is None:
        return jsonify({"error": "Товар не найден"}), 404

    return jsonify(product), 200


# Добавление товара
@app.route("/api/products", methods=["POST"])
def create_product():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Ожидается JSON-объект"}), 400

    name = data.get("name")
    price = data.get("price")
    description = data.get("description", "")

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "Укажите название товара"}), 400

    if (
        isinstance(price, bool)
        or not isinstance(price, (int, float))
        or price < 0
    ):
        return jsonify({"error": "Некорректная цена"}), 400

    new_id = max((p["id"] for p in products), default=0) + 1

    product = {
        "id": new_id,
        "name": name.strip(),
        "price": price,
        "description": description
    }

    products.append(product)

    return jsonify(product), 201


# Изменение товара
@app.route("/api/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    product = next(
        (p for p in products if p["id"] == product_id),
        None
    )

    if product is None:
        return jsonify({"error": "Товар не найден"}), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Ожидается JSON-объект"}), 400

    if "name" in data:
        if not isinstance(data["name"], str) or not data["name"].strip():
            return jsonify({"error": "Некорректное название"}), 400
        product["name"] = data["name"].strip()

    if "price" in data:
        price = data["price"]
        if (
            isinstance(price, bool)
            or not isinstance(price, (int, float))
            or price < 0
        ):
            return jsonify({"error": "Некорректная цена"}), 400
        product["price"] = price

    if "description" in data:
        if not isinstance(data["description"], str):
            return jsonify({"error": "Некорректное описание"}), 400
        product["description"] = data["description"]

    return jsonify(product), 200


# Удаление товара
@app.route("/api/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    product = next(
        (p for p in products if p["id"] == product_id),
        None
    )

    if product is None:
        return jsonify({"error": "Товар не найден"}), 404

    products.remove(product)

    return jsonify({
        "message": "Товар удалён",
        "id": product_id
    }), 200


# Информация о ферме
@app.route("/api/farm", methods=["GET"])
def get_farm():
    return jsonify(farm), 200


if __name__ == "__main__":
    app.run(debug=True)

