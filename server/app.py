from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)

@app.route('/restaurants', methods=['GET'])
def get_restaurants():
    restaurants = Restaurant.query.all()
    restaurants_list = [restaurant.to_dict(rules=('-pizzas',)) for restaurant in restaurants]
    return jsonify(restaurants_list)

@app.route('/restaurants/<int:id>', methods=['GET'])
def get_restaurant(id):
    restaurant = db.session.get(Restaurant, id)
    if restaurant is None:
        return jsonify({"error": "Restaurant not found"}), 404
    
    restaurant_data = restaurant.to_dict(rules=('-restaurant_pizzas.restaurant', 'restaurant_pizzas.pizza.ingredients', 'restaurant_pizzas.pizza.name', 'restaurant_pizzas.pizza.id', 'restaurant_pizzas.id', 'restaurant_pizzas.price', 'restaurant_pizzas.pizza_id', 'restaurant_pizzas.restaurant_id'))
    
    restaurant_data['restaurant_pizzas'] = [
        {
            "id": rp.id,
            "pizza_id": rp.pizza_id,
            "restaurant_id": rp.restaurant_id,
            "price": rp.price,
            "pizza": {
                "id": rp.pizza.id,
                "name": rp.pizza.name,
                "ingredients": rp.pizza.ingredients
            }
        } for rp in restaurant.restaurant_pizzas
    ]
    
    return jsonify(restaurant_data)


@app.route('/restaurants/<int:id>', methods=['DELETE'])
def delete_restaurant(id):
    restaurant = db.session.get(Restaurant, id)
    if restaurant is None:
        return jsonify({"error": "Restaurant not found"}), 404

    db.session.delete(restaurant)
    db.session.commit()

    return '', 204

@app.route('/pizzas', methods=['GET'])
def get_pizzas():
    pizzas = Pizza.query.all()
    pizzas_list = [pizza.to_dict(rules=('-restaurants',)) for pizza in pizzas]
    return jsonify(pizzas_list)

@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

@app.route('/restaurant_pizzas', methods=['POST'])
def create_restaurant_pizza():
    data = request.get_json()

    if not all(key in data for key in ['price', 'pizza_id', 'restaurant_id']):
        return jsonify({"errors": ["Missing data for required field(s)."]}), 400
    
   
    price = data.get('price')
    if not 1 <= price <= 30:
        return jsonify({"errors": ["validation errors"]}), 400

    
    new_restaurant_pizza = RestaurantPizza(
        price=data['price'],
        pizza_id=data['pizza_id'],
        restaurant_id=data['restaurant_id']
    )
    db.session.add(new_restaurant_pizza)
    try:
        db.session.commit()
    except Exception as e:
        return jsonify({"errors": [str(e)]}), 400

    result = db.session.get(RestaurantPizza, new_restaurant_pizza.id)
    return jsonify({
        "id": result.id,
        "price": result.price,
        "pizza_id": result.pizza_id,
        "restaurant_id": result.restaurant_id,
        "pizza": {
            "id": result.pizza.id,
            "ingredients": result.pizza.ingredients,
            "name": result.pizza.name
        },
        "restaurant": {
            "id": result.restaurant.id,
            "name": result.restaurant.name,
            "address": result.restaurant.address
        }
    }), 201

if __name__ == "__main__":
    app.run(port=5555, debug=True)