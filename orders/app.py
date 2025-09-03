import sqlite3
import os
import json
import requests
from flask import Flask, request
import hashlib
import hmac
import base64

app = Flask(__name__)

@app.route('/clear', methods=(['GET']))
def clear():
	return "Database Cleared"


@app.route("/order", methods=["POST"])
def order_product():
    order = request.form.get("order")
    order = json.loads(order)
    authorization = request.headers.get("Authorization")
    username, bool_val = verify_jwt(authorization)
    if bool_val == "Bad JWT":
        return json.dumps({"status": 2})
    
    total_cost = 0
    for items in order: #order is a list of dictionaries
        product_name = items["product"]
        product_quantity = items["quantity"]
        # Here you would typically check the product in your database and calculate the cost
        order_product_url = f"http://products:5000/get_product_for_order?product_name={product_name}"
        request_response = requests.get(url=order_product_url)
        data = request_response.json()
        if data["status"] != 1:
            return json.dumps({"status":3, "cost": "NULL"})
        order_log_url = "http://logs:5000/get_user"
        event = "order"
        requests.post(url=order_log_url, data={"username": username, "event": event})
        cost = data["price"]
        total_cost += cost * product_quantity
    
    total_cost = f"{total_cost:.2f}"
    return json.dumps({"status": 1, "cost": total_cost})


def verify_jwt(authorization):
    decoderURL = f"http://user:5000/get_decode?token={authorization}"
    response = requests.get(url = decoderURL)
    response = response.json()
    our_bool = response["our_bool"] 
    our_data = response["our_data"]
    username_retrieved = our_data["username"]
    if our_bool == False:
        return username_retrieved,"Bad JWT" 
    elif our_bool == True:
        return username_retrieved, True
    # datageturl = f"http://user:5000/get_employee_info?username={username_retrieved}"
    # new_response = requests.get(url = datageturl)
    # new_response = new_response.json()
    # if new_response["employee"] == "True":
    #     return username_retrieved, True
    # else:
    #     return username_retrieved, False

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)