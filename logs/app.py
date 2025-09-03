import sqlite3
import os
import json
import requests
from flask import Flask, request
import hashlib
import hmac
import base64

app = Flask(__name__)
db_name = "logs.db"
sql_file = "logs.sql"
db_flag = False

@app.route('/', methods=(['GET']))
def index():
	MICRO2URL = "http://localhost:9004/test_micro"
	r = requests.get(url = MICRO2URL)
	data = r.json()
	return data


@app.route('/test_micro', methods=(['GET']))
def test_micro():
	return "This is logs Microservice "

def create_db():
	conn = sqlite3.connect(db_name)
	with open(sql_file, 'r') as sql_startup:
		init_db = sql_startup.read()
	cursor = conn.cursor()
	cursor.executescript(init_db)
	conn.commit()
	conn.close()
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

@app.route('/get_user', methods=(['POST']))
def update_user_log():
	username = request.form.get("username")
	type_event = request.form.get("event")
	conn = get_db()
	cursor = conn.cursor()
	cursor.execute("INSERT INTO user_logs (username, type_event) VALUES (?, ?)", (username, type_event))
	conn.commit()
	conn.close()
	return "", 200

@app.route('/get_product_log', methods=(['POST']))
def update_product_log():
	conn = get_db()
	cursor = conn.cursor()
	username = request.form.get("username")
	event_type = request.form.get("event")
	product_name = request.form.get("product_name")
	cursor.execute("INSERT INTO product_logs (username, product_name, event_type) VALUES (?, ?, ?)", (username, product_name,event_type ))
	conn.commit()
	conn.close()
	return "", 200

@app.route("/view_log", methods=(['GET']))
def view_log():
	conn = get_db()
	cursor = conn.cursor()
	username = request.args.get("username")
	product = request.args.get("product")
	Authorization = request.headers.get("Authorization")

	getusername_url = f"http://user:5000/get_decode?token={Authorization}"
	response = requests.get(url=getusername_url)
	response = response.json()

	our_bool = response["our_bool"]
	our_data = response["our_data"]

	if our_bool == False:
		return json.dumps({"status": 2, "data": "NULL"})
	username_retrieved = our_data["username"]

	get_employee_url = f"http://user:5000/get_employee_info?username={username_retrieved}"
	response = requests.get(url=get_employee_url)
	response = response.json()

	employee_or_not = response["employee"]
	if employee_or_not == "True":
		if username != None:
			if username != username_retrieved:
				return json.dumps({"status": 3, "data": "NULL"})
			cursor.execute("SELECT username, type_event, time_user FROM user_logs WHERE username = ? ORDER BY time_user;", (username,))
			result1 = cursor.fetchall()

			cursor.execute("SELECT username, product_name, event_type, time_product FROM product_logs WHERE username = ? ORDER BY time_product;", (username,))
			result2 = cursor.fetchall()
			entire_list = []
			for item in result2:
				my_dict ={}
				my_dict["event"] = item[2]
				my_dict["user"] = item[0]
				my_dict["name"] = item[1]
				my_dict["time"] = item[3]
				entire_list.append(my_dict)

			for item in result1: 
				my_dict ={}
				my_dict["event"] = item[1]
				my_dict["user"] = item[0]
				my_dict["name"] = "NULL"
				my_dict["time"] = item[2]
				entire_list.append(my_dict)

			entire_list.sort(key=lambda x: x["time"])
			main_dict = {}
			for i, item in enumerate(entire_list):
				i = i+1
				my_dict ={}
				my_dict["event"] = item["event"]
				my_dict["user"] = item["user"]
				my_dict["name"] = item["name"]
				main_dict[i] = my_dict

			return json.dumps({"status": 1, "data": main_dict})
		elif product != None:
			cursor.execute("SELECT username, product_name, event_type FROM user_logs WHERE product_name = ? ORDER BY time_product;", (product,))
			result = cursor.fetchall()
			main_dict = {}
			for i, item in enumerate(result): 
				my_dict ={}
				my_dict["event"] = item[2]
				my_dict["user"] = item[0]
				my_dict["product"] = item[1]
				main_dict[i] = my_dict
			return json.dumps({"status": 1, "data": main_dict})
	elif employee_or_not == "False":
		if username != username_retrieved:
			return json.dumps({"status": 3, "data": "NULL"}) #a user can see his logs only
		if product != None:
			return json.dumps({"status": 3, "data": "NULL"}) #only employees can view product logs
		cursor.execute("SELECT username, type_event FROM user_logs WHERE username = ? ORDER BY time_user;", (username))
		result = cursor.fetchall()
		main_dict = {}
		for i, item in enumerate(result): 
			my_dict ={}
			my_dict["event"] = item[1]
			my_dict["user"] = item[0]
			my_dict["name"] = "NULL"
			main_dict[i] = my_dict
		return json.dumps({"status": 1, "data": main_dict})
	conn.commit()
	conn.close()

@app.route("/get_last_mod",methods=(["GET"]))
def give_last_mod():
	conn = get_db()
	cursor = conn.cursor()
	product_name = request.args.get("product_name")
	cursor.execute("SELECT username FROM product_logs WHERE product_name = ? ORDER BY time_product DESC LIMIT 1;",(product_name,))
	result = cursor.fetchone()
	conn.commit()
	conn.close()
	if result is not None:
		return json.dumps({"last_mod": result[0]})
	else:
		return json.dumps({"last_mod": "NULL"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)