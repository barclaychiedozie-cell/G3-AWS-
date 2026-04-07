const express = require("express");

const app = express();

app.use(express.json());

// Home route
app.get("/", (req, res) => {
  res.send("Server Working");
});

// Admin - Get Users
app.get("/api/admin/users", (req, res) => {
  res.json({
    users: [
      { name: "Patient1", role: "patient" },
      { name: "Clinician1", role: "clinician" }
    ]
  });
});

// Admin - Create User
app.post("/api/admin/create-user", (req, res) => {
  const { name, email, role } = req.body;

  res.json({
    message: "User created",
    user: { name, email, role }
  });
});

// Start server
app.listen(3000, () => {
  console.log("SERVER STARTED ON 3000");
});