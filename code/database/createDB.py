import sqlite3

conn = sqlite3.connect("userDB.db")

cur = conn.cursor()

create_table_query = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    avatar TEXT NOT NULL
);
"""

cur.execute(create_table_query)

insert_query = """
INSERT INTO users (username, password, avatar)
    VALUES (?, ?, ?)
    """

cur.execute(insert_query, ("user01", "user01", "1"))
cur.execute(insert_query, ("user02", "user02", "2"))
cur.execute(insert_query, ("user03", "user03", "3"))


conn.commit()
conn.close()
