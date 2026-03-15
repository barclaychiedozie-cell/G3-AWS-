# G3-AWS-
This Is The Repository for Group3's Advanced Web Solution Project

## Healthcare Management System

A Django GraphQL application for managing patients and clinicians.

### Implemented User Stories

1. **As a clinician, I want to see a list of patients so that I can select who to review**
   - GraphQL API for querying patient lists
   - Search and filter functionality
   - Comprehensive patient profiles

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
