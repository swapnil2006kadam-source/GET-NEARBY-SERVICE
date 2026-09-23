import mysql.connector
import getpass

password = getpass.getpass("Enter Aiven MySQL password: ")

conn = mysql.connector.connect(
    host="mysql-26a33d1b-kamblesujit600-5bc5.l.aivencloud.com",
    port=19806,
    user="avnadmin",
    password=password,
    database="defaultdb",
    ssl_ca="ca.pem"
)

cursor = conn.cursor()

sql = """
INSERT INTO users (name, email, password, role)
VALUES ('Admin', 'admin@getnearby.com', 'admin123', 'admin')
"""

cursor.execute(sql)
conn.commit()

print("ADMIN CREATED SUCCESSFULLY!")

cursor.close()
conn.close()