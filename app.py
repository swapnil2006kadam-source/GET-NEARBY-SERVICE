from flask import Flask, render_template, request, redirect, jsonify, session
from config.database import connection, cursor

import os
import requests

from dotenv import load_dotenv

load_dotenv()

GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")


app = Flask(__name__)

app.secret_key = "get_nearby_services_secret_key"


# ---------------- HOME ---------------- #

@app.route("/")
def home():
    return render_template("home.html")


# ---------------- REGISTER ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():

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

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        cursor.execute(
            """
            SELECT * FROM users
            WHERE email=%s
            AND password=%s
            AND role='user'
            """,
            (email, password)
        )

        user = cursor.fetchone()

        if user:

            session["user_id"] = user[0]
            session["user_name"] = user[1]
            session["role"] = user[4]

            return redirect("/dashboard")

        return "Invalid User Login"

    return render_template("login.html")


# ---------------- ADMIN LOGIN ---------------- #

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

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

    data = request.get_json()

    latitude = data["latitude"]
    longitude = data["longitude"]

    user_id = session["user_id"]

    cursor.execute(
    """
    INSERT INTO user_locations
    (user_id, latitude, longitude)
    VALUES(%s,%s,%s)
    """,
    (user_id, latitude, longitude)
)

    connection.commit()

    return jsonify({
        "status": "success"
    })


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)