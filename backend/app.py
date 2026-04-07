from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# ================= FRONTEND =================

@app.route("/")
def home():
    return render_template("index.html")

# ================= ADMIN APIs =================

# Get Users
@app.route("/api/admin/users", methods=["GET"])
def get_users():
    return jsonify({
        "users": [
            {"name": "Patient1", "role": "patient"},
            {"name": "Clinician1", "role": "clinician"}
        ]
    })

# Create User
@app.route("/api/admin/create-user", methods=["POST"])
def create_user():
    data = request.get_json()
    return jsonify({
        "message": "User created successfully",
        "user": data
    })

# Assign Role
@app.route("/api/admin/assign-role", methods=["PUT"])
def assign_role():
    data = request.get_json()
    return jsonify({
        "message": "Role assigned successfully",
        "data": data
    })

# Assign Clinician
@app.route("/api/admin/assign-clinician", methods=["POST"])
def assign_clinician():
    data = request.get_json()
    return jsonify({
        "message": "Clinician assigned to patient",
        "data": data
    })

# Upload Patient Data (FIXED)
@app.route("/api/admin/upload-data", methods=["POST"])
def upload_data():
    data = request.get_json()
    return jsonify({
        "message": "Patient data uploaded successfully",
        "data": data
    })

# Logout (FIXED)
@app.route("/api/admin/logout", methods=["POST"])
def logout():
    return jsonify({
        "message": "Logout successful. Session ended."
    })

# ================= RUN =================

if __name__ == "__main__":
    app.run(port=3000)