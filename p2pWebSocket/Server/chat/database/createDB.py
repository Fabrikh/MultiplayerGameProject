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

conn.commit()
conn.close()
