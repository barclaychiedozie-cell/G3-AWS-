from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Server Working"

@app.route("/api/admin/users", methods=["GET"])
def get_users():
    return jsonify({
        "users": [
            {"name": "Patient1", "role": "patient"},
            {"name": "Clinician1", "role": "clinician"}
        ]
    })

@app.route("/api/admin/create-user", methods=["POST"])
def create_user():
    data = request.get_json()
    return jsonify({
        "message": "User created",
        "user": data
    })

@app.route("/api/admin/assign-role", methods=["PUT"])
def assign_role():
    data = request.get_json()
    return jsonify({
        "message": "Role assigned",
        "data": data
    })

@app.route("/api/admin/upload-data", methods=["POST"])
def upload_data():
    return jsonify({
        "message": "Patient data uploaded"
    })

@app.route("/api/admin/logout", methods=["POST"])
def logout():
    return jsonify({
        "message": "Logged out successfully"
    })

if __name__ == "__main__":
    app.run(port=3000)
