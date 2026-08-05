from flask import Flask, render_template, request, redirect, jsonify, session
from config.database import get_connection
from datetime import datetime
import os
import requests
from flask_mail import Mail, Message
import random , time

from dotenv import load_dotenv

load_dotenv()

GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")


app = Flask(__name__)
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT"))
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS") == "True"
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

mail = Mail(app)


app.secret_key = "get_nearby_services_secret_key"


# ---------------- HOME ---------------- #

@app.route("/")
def home():
    return render_template("home.html")


# ---------------- REGISTER ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():

    connection, cursor = get_connection()

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        cursor.execute(
            """
            INSERT INTO users(name,email,password,role)
            VALUES(%s,%s,%s,'user')
            """,
            (name, email, password)
        )

        connection.commit()

        return redirect("/login")

    return render_template("register.html")


# ---------------- USER LOGIN ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    connection, cursor = get_connection()

    email = request.form["email"]
    password = request.form["password"]

    cursor.execute("""
        SELECT *
        FROM users
        WHERE email=%s
        AND password=%s
        AND role='user'
    """, (email, password))

    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if not user:
        return jsonify({
            "status": "error",
            "message": "Invalid Email or Password"
        })

    otp = random.randint(100000, 999999)

    session["login_otp"] = str(otp)
    session["otp_user"] = user[0]
    session["otp_name"] = user[1]
    session["otp_role"] = user[4]
    session["otp_time"] = time.time()

    msg = Message(
        subject="Nearby Services Login OTP",
        recipients=[email]
    )

    msg.body = f"""
Hello {user[1]},

Your OTP is:

{otp}

This OTP is valid for 5 minutes.

Regards,
GetNearby Team
"""

    try:

        print("Sending OTP...")
        mail.send(msg)
        print("OTP Sent Successfully")

    except Exception as e:

        print("MAIL ERROR:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        })

    return jsonify({
        "status": "success",
        "email": email
    })

@app.route("/verify-login-otp", methods=["POST"])
def verify_login_otp():

    entered = request.form["otp"]

    if "login_otp" not in session:
        return jsonify({
            "status": "error",
            "message": "Session Expired"
        })

    if time.time() - session["otp_time"] > 300:

        return jsonify({
            "status": "error",
            "message": "OTP Expired"
        })

    if entered != session["login_otp"]:

        return jsonify({
            "status": "error",
            "message": "Invalid OTP"
        })

    session["user_id"] = session["otp_user"]
    session["user_name"] = session["otp_name"]
    session["role"] = session["otp_role"]

    session.pop("login_otp")
    session.pop("otp_user")
    session.pop("otp_name")
    session.pop("otp_role")
    session.pop("otp_time")

    return jsonify({
        "status": "success"
    })

# ---------------- ADMIN LOGIN ---------------- #

@app.route("/admin-login", methods=["GET","POST"])
def admin_login():

    connection, cursor = get_connection()

    if request.method=="POST":

        email = request.form["email"]
        password = request.form["password"]

        cursor.execute(
            """
            SELECT * FROM users
            WHERE email=%s
            AND password=%s
            AND role='admin'
            """,
            (email, password)
        )

        admin = cursor.fetchone()
        print("EMAIL:", email)
        print("PASSWORD:", password)
        print("ADMIN:", admin)

        if admin:

            session["admin_id"] = admin[0]
            session["admin_name"] = admin[1]
            session["role"] = admin[4]

            return redirect("/admin-dashboard")

        return "Invalid Admin Login"

    return render_template("admin_login.html")


# ---------------- USER DASHBOARD ---------------- #

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect("/login")

    return render_template(
        "dashboard.html",
        name=session["user_name"]
    )


# ---------------- ADMIN DASHBOARD ---------------- #

@app.route("/admin-dashboard")
def admin_dashboard():
    connection, cursor = get_connection()

    if "admin_id" not in session:
        return redirect("/admin-login")


    # Latest Location
    cursor.execute("""
        SELECT
            users.name,
            users.email,
            user_locations.latitude,
            user_locations.longitude,
            user_locations.created_at
        FROM user_locations
        JOIN users
        ON users.id = user_locations.user_id
        ORDER BY user_locations.id DESC
        LIMIT 1
    """)

    latest = cursor.fetchone()

    # History
    cursor.execute("""
        SELECT
            users.name,
            users.email,
            user_locations.latitude,
            user_locations.longitude,
            user_locations.created_at
        FROM user_locations
        JOIN users
        ON users.id = user_locations.user_id
        ORDER BY user_locations.id DESC
    """)

    history = cursor.fetchall()

    # Total Users
    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE role='user'
    """)
    total_users = cursor.fetchone()[0]

    # Total Locations
    cursor.execute("""
        SELECT COUNT(*)
        FROM user_locations
    """)
    total_locations = cursor.fetchone()[0]

    return render_template(
        "admin_dashboard.html",
        location=latest,
        history=history,
        total_users=total_users,
        total_locations=total_locations
    )

@app.route("/live-locations")
def live_locations():
    connection, cursor = get_connection()

    if "admin_id" not in session:
        return jsonify([])

    

    cursor.execute("""
        SELECT
            users.id,
            users.name,
            users.email,
            user_locations.latitude,
            user_locations.longitude,
            user_locations.created_at

        FROM users

        JOIN user_locations
        ON users.id = user_locations.user_id

        WHERE users.role='user'

        ORDER BY users.name
    """)

    rows = cursor.fetchall()

    users = []

    for row in rows:

        last_seen = row[5]

        seconds = int((datetime.now() - last_seen).total_seconds())

        if seconds <= 30:
            status = "Online"
        else:
            status = "Offline"

        users.append({

            "id": row[0],
            "name": row[1],
            "email": row[2],
            "lat": float(row[3]),
            "lon": float(row[4]),
            "time": str(last_seen),
            "seconds": seconds,
            "status": status

        })

    return jsonify(users)

# ---------------- NEARBY ---------------- #

@app.route("/nearby")
def nearby():

    if "user_id" not in session:

        return redirect("/login")

    return render_template("nearby.html")

@app.route("/get-nearby")
def get_nearby():

    category = request.args.get("category")
    latitude = request.args.get("lat")
    longitude = request.args.get("lon")

    category_map = {
    "hospital": "healthcare.hospital",
    "restaurant": "catering.restaurant",
    "mall": "commercial.shopping_mall",
    "pharmacy": "healthcare.pharmacy",
    "fuel": "service.vehicle.fuel"
}

    place = category_map.get(category)

    if not place:
        return jsonify([])

    url = (
        f"https://api.geoapify.com/v2/places?"
        f"categories={place}"
        f"&filter=circle:{longitude},{latitude},3000"
        f"&bias=proximity:{longitude},{latitude}"
        f"&limit=40"
        f"&apiKey={GEOAPIFY_API_KEY}"
    )

    response = requests.get(url)

    print(url)
    print(response.status_code)
    print(response.text)

    data = response.json()

    places = []

    for item in data.get("features", []):

        properties = item["properties"]

        name = (
            properties.get("name")
            or properties.get("address_line1")
            or properties.get("formatted")
        )

        if not name:

            if category == "hospital":
                name = "Nearby Hospital"

            elif category == "restaurant":
                name = "Nearby Restaurant"

            elif category == "mall":
                name = "Shopping Mall"

            elif category == "pharmacy":
                name = "Nearby Pharmacy"

            elif category == "fuel":
                name = "Nearby Petrol Pump"

            else:
                name = "Unknown Place"

        places.append({

            "name": name,

            "lat": properties["lat"],

            "lon": properties["lon"],

            "address": properties.get("formatted", ""),

            "distance": properties.get("distance", 0)

        })

    return jsonify(places)


# ---------------- SAVE LOCATION ---------------- #

@app.route("/save-location", methods=["POST"])
def save_location():
    connection, cursor = get_connection()

    data = request.get_json()

    latitude = data["latitude"]
    longitude = data["longitude"]

    user_id = session["user_id"]


    cursor.execute("""
    INSERT INTO user_locations
    (user_id, latitude, longitude)
    VALUES (%s, %s, %s)

    ON DUPLICATE KEY UPDATE
    latitude = VALUES(latitude),
    longitude = VALUES(longitude),
    created_at = CURRENT_TIMESTAMP
    """, (user_id, latitude, longitude))

    connection.commit()

    return jsonify({
        "status": "success"
    })

# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# DELETE LOCATION
@app.route("/delete-location/<int:user_id>", methods=["POST"])
def delete_location(user_id):
    connection, cursor = get_connection()

    if "admin_id" not in session:
        return jsonify({"status": "unauthorized"}), 401


    cursor.execute("""
        DELETE FROM user_locations
        WHERE user_id=%s
    """, (user_id,))

    connection.commit()

    return jsonify({
        "status": "success"
    })

@app.route("/welcome")
def welcome():

    return render_template("welcome.html")
    
if __name__ == "__main__":
    app.run(debug=True)
