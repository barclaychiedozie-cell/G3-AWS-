# G3-AWS-
This Is The Repository for Group3's Advanced Web Solution Project

## Healthcare Management System

A Django GraphQL application for managing patients and clinicians.

### User Stories

1. **As a patient, I want to receive notifications when my pressure is too high so that I can adjust my sitting position.**
   - Real-time pressure monitoring alerts
   - Threshold settings for high pressure
   - Visual and/or email notification support

2. **As a clinician, I want to see a list of patients so that I can select who to review.**
   - GraphQL API for querying patient lists
   - Search and filter functionality
   - Comprehensive patient profiles

3. **As a clinician, I want to read patient comments linked to specific data points so that I can better understand their discomfort.**
   - Comments attached to readings or events
   - Timeline view for context
   - Queryable via API

4. **As an admin, I want to assign roles so that users have the correct permissions.**
   - Role-based access control
   - Admin UI for role assignment
   - Permission checks in APIs

### Features

- Patient and Clinician management
- GraphQL API with GraphiQL interface
- Django Admin interface
- SQLite database (development)

### Getting Started

1. Navigate to the graphene_trace directory:
   ```bash
   cd graphene_trace
   ```

2. Install dependencies:
   ```bash
   pip install graphene-django
   ```

3. Run migrations:
   ```bash
   python manage.py migrate
   ```

4. Start the server:
   ```bash
   python manage.py runserver
   ```

5. Access:
   - GraphQL API: http://localhost:8000/graphql/
   - Django Admin: http://localhost:8000/admin/

### API Documentation

See `healthcare/README.md` for detailed GraphQL query examples and API documentation.
