import mysql.connector
import os
from getpass import getpass

host = "mysql-26a33d1b-kamblesujit600-5bc5.l.aivencloud.com"
port = 19806
user = "avnadmin"
database = "defaultdb"

password = getpass("Enter Aiven MySQL password: ")

conn = mysql.connector.connect(
    host=host,
    port=port,
    user=user,
    password=password,
    database=database,
    ssl_ca="ca.pem"
)

cursor = conn.cursor()

with open("database/schema.sql", "r", encoding="utf-8") as f:
    sql = f.read()

for statement in sql.split(";"):
    statement = statement.strip()
    if statement:
        cursor.execute(statement)

conn.commit()

cursor.execute("SHOW TABLES")
print("\nTables created:")
for table in cursor.fetchall():
    print(table[0])

cursor.close()
conn.close()

print("\nSUCCESS! Aiven database is ready.")