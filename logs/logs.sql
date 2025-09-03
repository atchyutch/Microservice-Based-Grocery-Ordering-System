DROP TABLE IF EXISTS user_logs;
CREATE TABLE user_logs (
    username TEXT,
    type_event TEXT,
    time_user TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
);


DROP TABLE IF EXISTS product_logs;
CREATE TABLE product_logs(
    username TEXT,
    product_name TEXT,
    event_type TEXT,
    time_product TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
    FOREIGN KEY (username) REFERENCES user_log(username)
);  
