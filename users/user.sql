DROP TABLE IF EXISTS user_details;
CREATE TABLE user_details (
    first_name TEXT,
    last_name TEXT,
    username TEXT NOT NULL UNIQUE,
    email_address TEXT NOT NULL UNIQUE,
    password TEXT,
    salt TEXT,
    employee TEXT,
    PRIMARY KEY (username, email_address)
);


DROP TABLE IF EXISTS user_passwords;
CREATE TABLE user_passwords (
    username TEXT,
    previous_password TEXT, 
    FOREIGN KEY(username) REFERENCES user_details(username) ON DELETE CASCADE
);