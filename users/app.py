import sqlite3
import os
import json
import requests
from flask import Flask, request, jsonify
import hashlib
import hmac
import base64


app = Flask(__name__)
db_name = "user.db"
sql_file = "user.sql"
db_flag = False

@app.route('/', methods=(['GET']))
def index():
	MICRO2URL = "http://localhost:5001/test_micro"
	r = requests.get(url = MICRO2URL)
	data = r.json()
	return data


@app.route('/test_micro', methods=(['GET']))
def test_micro():
	return "This is user Microservice "


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

@app.route('/create_user', methods=(['POST']))
def create_user():
	conn = get_db()
	cursor = conn.cursor()
	try:
		firstname = request.form.get('first_name')
		lastname = request.form.get('last_name')
		username = request.form.get('username')
		email_address = request.form.get('email_address')
		password = request.form.get('password')
		salt = request.form.get('salt')
		employee = request.form.get('employee')
		

		if verify_password(password,firstname,username,lastname,salt) == True:
			password_stored = hash_password(salt, password)
		else:
			return json.dumps({"status": 4, "pass_hash": "NULL"})
		
		cursor.execute("INSERT INTO user_details(first_name, last_name, username, email_address, password, salt,employee) VALUES(?,?,?,?,?,?,?);",
					(firstname, lastname, username, email_address, password_stored,salt,employee))
		
		event = "user_creation"
		urltosend = "http://logs:5000/get_user"
		datatosend = {"username": username, "event": event}
		r = requests.post(url = urltosend, data = datatosend) # just sends the data to the logs microservice  # this does not return anything
		
		cursor.execute("INSERT INTO user_passwords(username, previous_password) VALUES(?,?);",
					(username, password_stored))
		conn.commit()
		return json.dumps({"status": 1, "pass_hash": password_stored})

	except sqlite3.IntegrityError as e:
		if ("UNIQUE constraint failed: user_details.username" in str(e)):
			return json.dumps({"status": 2, "pass_hash": "NULL"})
		elif ("UNIQUE constraint failed: user_details.email_address" in str(e)):
			return json.dumps({"status": 3, "pass_hash": "NULL"})
	finally:
		conn.close()


def verify_password(password,firstname,username,lastname,salt):
	if (firstname in password) or (username in password) or (lastname in password):
		return False
	if len(password) < 8:
		return False
	has_upper = False
	has_lower = False
	has_digit = False
	if any(c.isupper() for c in password):
		has_upper = True
	if any(c.islower() for c in password):
		has_lower = True
	if any(c.isdigit() for c in password):
		has_digit = True
	if user_previous_passwords(username, password, salt) == False:
		return False
	if has_upper and has_lower and has_digit:
		return True
	else:
		return False


def hash_password(salt, password): 
	password_salt = (password + salt).encode()
	hashed_password = hashlib.sha256(password_salt).hexdigest()
	return hashed_password


def user_previous_passwords(username, password, salt):
	conn = get_db()
	cursor = conn.cursor()
	password = hash_password(salt, password)
	cursor.execute("SELECT previous_password FROM user_passwords WHERE username = ?;", (username,))
	result2 = cursor.fetchall() 
	for hash in result2:
		if password == hash[0]:
			return False
	conn.commit()
	conn.close()
	return True


@app.route('/login', methods=(['POST']))
def login_user():
	username = request.form.get('username')
	password = request.form.get('password')

	conn = get_db()
	cursor = conn.cursor()

	cursor.execute("SELECT password FROM user_details WHERE username = ?;",(username,))
	retrieved_password = cursor.fetchone()
	cursor.execute("SELECT salt FROM user_details WHERE username = ?;",(username,))
	retrieved_salt = cursor.fetchone() 
	
	password_calculated = hash_password(retrieved_salt[0], password)

	if password_calculated == retrieved_password[0]:  
		header = {"alg": "HS256" , "typ": "JWT"}
		payload = {"username": username}

		header_json = json.dumps(header)
		payload_json = json.dumps(payload, sort_keys = False)
		
		encoded_header = base64.urlsafe_b64encode(header_json.encode('utf-8')).decode('utf-8')
		encoded_payload = base64.urlsafe_b64encode(payload_json.encode('utf-8')).decode('utf-8')


		event = "login"
		urltosendinlogin = "http://logs:5000/get_user"
		datatologin = {"username": username, "event": event}
		r = requests.post(url = urltosendinlogin, data = datatologin) # just send the data to the logs microservice  # this does not return anything
		
		
		return json.dumps({"status": 1, "jwt": create_jwt(encoded_header,encoded_payload)})
		
	elif password_calculated != retrieved_password[0]:
		return json.dumps({"status": 2, "jwt": "NULL"})
	conn.commit()
	conn.close()


def create_jwt(encoded_header,encoded_payload): 
	with open('key.txt' , 'r') as key:
		key = key.read().strip()
	join_header_payload = f"{encoded_header}.{encoded_payload}"
	signature = hmac.new(key.encode('utf-8'), join_header_payload.encode('utf-8'), hashlib.sha256).hexdigest()
	jwt_token = f"{join_header_payload}.{signature}"
	return jwt_token


def decode_jwt(jwt_token):
	with open('key.txt', 'r') as key:
		key = key.read().strip()
	jwt_list = jwt_token.split('.')

	header_jwt = jwt_list[0]
	payload_jwt = jwt_list[1]
	signature_jwt = jwt_list[2]

	header_bytes = (base64.urlsafe_b64decode((header_jwt).encode('utf-8')))
	payload_bytes = (base64.urlsafe_b64decode((payload_jwt).encode('utf-8')))
	
	decoded_header = (header_bytes).decode('utf-8')
	decoded_payload = (payload_bytes).decode('utf-8')
	
	header_data = json.loads(decoded_header)
	payload_data = json.loads(decoded_payload) 

	header_data = json.dumps(header_data) #this is converting the dictionary to a json string
	payload_data = json.dumps(payload_data, sort_keys = False)

	join_header_payload = f"{header_jwt}.{payload_jwt}"
	newly_created_signature = hmac.new(key.encode('utf-8'), join_header_payload.encode('utf-8'), hashlib.sha256).hexdigest()
	if newly_created_signature == signature_jwt:
		return True, json.loads(payload_data)
	else:
		return False, json.loads(payload_data)

@app.route("/get_decode", methods=['GET'])
def give_decode():
	token = request.args.get("token")
	value1, value2 = decode_jwt(token)
	return jsonify({"our_bool":value1, "our_data": value2})

@app.route("/get_employee_info", methods=['GET'])
def get_data_user():
	conn = get_db()
	cursor = conn.cursor()
	username = request.args.get("username")
	cursor.execute("SELECT employee FROM user_details WHERE username = ?;", (username,))
	result = cursor.fetchone() # data is a list with one element right?  
	conn.commit()
	conn.close()
	return jsonify({"employee":result[0]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


