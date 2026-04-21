# G3-AWS-
This Is The Repository for Group3's Advanced Web Solution Project
# G3-AWS — Graphene Trace

This is the repository for Group 3's Advanced Web Solution project.

Graphene Trace is a Django-based web application for managing pressure sensor data for patients, with role-based access for admins, clinicians, and patients.

---

## Tech Stack

- Python 3.11
- Django 5.1
- SQLite (development database)
- HTML/CSS/JavaScript (frontend)

---

## Project Structure

```
graphene_trace/
├── users/              # Custom user model, role management, seed command
├── patients/           # Pressure data, uploads, comments, messages, notifications
├── clinicians/         # Clinician-patient access control
├── admin_dashboard/    # Admin proxy models for site administration
├── templates/          # HTML templates (base, admin, patient, clinician views)
├── static/             # CSS, JS, vendor assets
└── manage.py
```

---

## Admin Features Implemented

The following admin capabilities have been built into the Django admin site (`/admin/`):

- **Logout** — secure POST-based logout button in the admin header
- **User Account Management** — create, edit, activate and deactivate user accounts
- **Role Assignment** — assign admin, clinician, or patient roles to any user
- **Clinician–Patient Access Control** — assign and revoke clinician access to patients, with duplicate validation
- **Patient Data Upload** — upload CSV pressure sensor data for patients, with file validation (extension, MIME type, empty file check) and automatic row/column metadata recording

---

## How to Run

1. Open a terminal in the `graphene_trace` folder:

```cmd
cd G3-AWS-\graphene_trace
```

2. Activate the virtual environment (use Command Prompt, not PowerShell):

```cmd
.venv\Scripts\activate.bat
```

3. Apply database migrations:

```cmd
python manage.py migrate
```

4. Create the default admin account:

```cmd
python manage.py seed_admin
```

5. Start the development server:

```cmd
python manage.py runserver
```

6. Open your browser and go to:

- Main site: `http://127.0.0.1:8000/`
- Admin panel: `http://127.0.0.1:8000/admin/`

---

## Default Admin Credentials

| Username | Password |
|----------|----------|
| ajay     | ajay123  |

To reset the password at any time:

```cmd
python manage.py changepassword ajay
```

---

## User Roles

| Role      | Access                                      |
|-----------|---------------------------------------------|
| admin     | Full access via Django admin panel          |
| clinician | Clinician dashboard, assigned patients only |
| patient   | Patient dashboard, own data only            |
