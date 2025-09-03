import sqlite3
import os
import json
import requests
from flask import Flask, request
import hashlib
import hmac
import base64

app = Flask(__name__)
db_name = "products.db"
sql_file = "products.sql"
db_flag = False

@app.route('/', methods=(['GET']))
def index():
	return json.dumps({'1': 'test', '2': 'test2'})

@app.route('/test_micro', methods=(['GET']))
def test_micro():

	return json.dumps({"response": "This is a message from Microservice 2"})


def create_db():
	conn = sqlite3.connect(db_name)
	with open(sql_file, 'r') as sql_startup:
		init_db = sql_startup.read()
	cursor = conn.cursor()
	cursor.executescript(init_db)
	conn.commit()
	global db_flag
	db_flag = True
	return conn

def get_db():
	if not db_flag:
		create_db()
	conn = sqlite3.connect(db_name)
	return conn

@app.route('/clear', methods=(['GET']))
def clear():
	if os.path.exists(db_name):
		os.remove(db_name)
	else:
		None
	create_db()
	return "Database Cleared"

@app.route('/create_product', methods=(['POST']))
def create_product():
	conn = get_db()
	cursor = conn.cursor()
	name = request.form.get("name")
	price = request.form.get("price")
	category = request.form.get("category")
	Authorization = request.headers.get("Authorization")

	usernametosend, val_bool = verify_employee(Authorization)
	if val_bool == False:
		return json.dumps({"status": 2})
	if val_bool == "Bad JWT":
		return json.dumps({"status": 2})
	cursor.execute("INSERT INTO product_details (name, price, category) VALUES(?,?,?);", (name, price, category))

	event_type = "product_creation"
	data = {"product_name":name, "event": event_type, "username": usernametosend}
	urltosend = "http://logs:5000/get_product_log"
	requests.post(url = urltosend, data = data)

	conn.commit()
	conn.close()
	return json.dumps({"status": 1})


def verify_employee(authorization):  # give me if the user is employee or not
	decoderURL = f"http://user:5000/get_decode?token={authorization}"
	response = requests.get(url = decoderURL)
	response = response.json()
	our_bool = response["our_bool"] 
	our_data = response["our_data"]
	username_retrieved = our_data["username"]
	if our_bool == False:
		return username_retrieved,"Bad JWT" 
	
	datageturl = f"http://user:5000/get_employee_info?username={username_retrieved}"
	new_response = requests.get(url = datageturl)
	new_response = new_response.json()
	if new_response["employee"] == "True":
		return username_retrieved, True
	else:
		return username_retrieved, False

@app.route('/edit_product', methods=(['POST']))
def edit_product():
	conn = get_db()
	cursor = conn.cursor()
	name = request.form.get("name")
	new_price = request.form.get("new_price")
	new_category = request.form.get("new_category")
	Authorization = request.headers.get("Authorization")

	usernametosend, bool = verify_employee(Authorization)
	if bool == "Bad JWT":
		return json.dumps({"status": 2})
	if bool == False:
		return json.dumps({"status": 3})
	
	cursor.execute("UPDATE product_details SET price = ?, category = ? WHERE name = ?;", (new_price, new_category, name))

	event_type = "product_edit"
	data = {"product_name":name, "event": event_type, "username": usernametosend}
	urltosend = "http://logs:5000/get_product_log"
	requests.post(url = urltosend, data = data)

	conn.commit()
	conn.close()
	return json.dumps({"status": 1})

@app.route("/get_product", methods=(['GET']))
def get_products():
	conn = get_db()
	cursor = conn.cursor()

	product_name = request.args.get("product_name")
	category = request.args.get("category")

	if product_name != None:
		cursor.execute("SELECT * FROM product_details WHERE name = ?;", (product_name,))
		product_data = cursor.fetchone() # this is a list with three values #this couyld be like this([name, category, price])
		if product_data == None:
			return json.dumps({"status": 2})
		else:
			#lets get the last modifier.
			mod_url = f"http://logs:5000/get_last_mod?product_name={product_name}"
			mod_response = requests.get(url=mod_url)
			mod_response = mod_response.json() 
			mod_response = mod_response["last_mod"]
			data_list = []
			data_list.append({"product_name": product_data[0], "price": product_data[2], "category": product_data[1], "last_mod": mod_response}) # this is 0,2,1 becuase the price is the last column in the sql file  # makes sense?  
			return json.dumps({"status": 1, "data": data_list})
	elif category != None:
		cursor.execute("SELECT * FROM product_details WHERE category = ?;", (category,))
		product_data = cursor.fetchall()
		if product_data == ():
			return json.dumps({"status": 2})
		else:
			data_list = []
			for list_1 in product_data:
				product_name = list_1[0]
				mod_url  = f"http://logs:5000/get_last_mod?product_name={product_name}"
				mod_response = requests.get(url=mod_url)
				mod_response = mod_response.json()
				mod_response = mod_response["last_mod"]

				data_list.append({"product_name": list_1[0], "price": list_1[2], "category": list_1[1], "last_mod": mod_response}) 
			return json.dumps({"status": 1, "data": data_list})


@app.route("/get_product_for_order", methods=(['GET']))
def get_product_for_order():
	conn = get_db()
	cursor = conn.cursor()

	product_name = request.args.get("product_name")
	cursor.execute("SELECT price FROM product_details WHERE NAME = ?;", (product_name,))
	product_data = cursor.fetchone()
	if product_data == None:
		return json.dumps({"status": 3})
	else:
		price = product_data[0]
		return json.dumps({"status": 1, "price": price})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)