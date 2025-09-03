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

@app.route("/search", methods=["GET"])
def search_details():
    product_name = request.args.get("product_name")
    category = request.args.get("category")
    Authorization = request.headers.get("Authorization")
    
    #lets begin with the jwt verification
    urlfordetails = f"http://user:5000/get_decode?token={Authorization}"
    response = requests.get(url=urlfordetails)
    response = response.json()
    our_bool = response["our_bool"]
    our_data = response["our_data"]
    if our_bool == False:
        return json.dumps({"status": 2})
    username_retrieved = our_data["username"]

    #lets get product details
    # lets send the product name or category to the product microservice
    if product_name != None:
        producturl = f"http://products:5000/get_product?product_name={product_name}"
        product_response = requests.get(url=producturl)
        product_response = product_response.json()
        # send data to logs now

        event_type = "search"
        data = {"event": event_type, "username": username_retrieved, "product_name": product_name}
        sendtolog = "http://logs:5000/get_product_log"
        requests.post(url = sendtolog, data = data)

        if product_response["status"] == 2:
            return json.dumps({"status": 3})
        elif product_response["status"] == 1:
            return json.dumps({"status": 1, "data": product_response["data"]})
        
    elif category != None:
        event_type = "search"
        categoryurl = f"http://products:5000/get_product?category={category}"
        category_response = requests.get(url=categoryurl)
        category_response = category_response.json()

        # event_type = "search"
        # dataforcat = {"event": event_type, "username": username_retrieved, "product_name": "NULL" }
        # sendtolog = "https://logs:5000/get_product"
        # requests.post(url = sendtolog, data = dataforcat)

        if category_response["status"] == 2:
            return json.dumps({"status": 3})
        elif category_response["status"] == 1:
            return json.dumps({"status": 1, "data": category_response["data"]})
        

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)