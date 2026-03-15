# Healthcare Management System

This Django application provides a GraphQL API for managing patients and clinicians in a healthcare setting.

## User Story Implemented

**As a clinician, I want to see a list of patients so that I can select who to review**

## Features

- Patient management with comprehensive profiles
- Clinician management with specialties and licensing
- GraphQL API for querying patient and clinician data
- Django Admin interface for data management

## GraphQL API

The GraphQL endpoint is available at `/graphql/` with GraphiQL interface enabled for testing.

### Available Queries

#### Get All Patients
```graphql
query {
  patients {
    id
    firstName
    lastName
    email
    medicalRecordNumber
    age
    phone
    dateOfBirth
    address
    emergencyContactName
    emergencyContactPhone
    createdAt
  }
}
```

#### Search Patients
```graphql
query {
  patients(search: "john") {
    id
    firstName
    lastName
    medicalRecordNumber
    age
  }
}
```

#### Get Patient Count
```graphql
query {
  patientCount
}
```

#### Get Specific Patient
```graphql
query {
  patient(id: "1") {
    id
    firstName
    lastName
    medicalRecordNumber
    age
  }
}
```

#### Get Clinicians
```graphql
query {
  clinicians {
    id
    firstName
    lastName
    specialty
    licenseNumber
    email
    phone
  }
}
```

#### Get Clinicians by Specialty
```graphql
query {
  clinicians(specialty: "Cardiology") {
    id
    firstName
    lastName
    specialty
  }
}
```

### Available Mutations

#### Create Patient
```graphql
mutation {
  createPatient(
    firstName: "John"
    lastName: "Doe"
    email: "john.doe@example.com"
    dateOfBirth: "1980-01-01"
    medicalRecordNumber: "MRN001"
    phone: "+1234567890"
    address: "123 Main St"
    emergencyContactName: "Jane Doe"
    emergencyContactPhone: "+0987654321"
  ) {
    patient {
      id
      firstName
      lastName
      medicalRecordNumber
    }
  }
}
```

#### Create Clinician
```graphql
mutation {
  createClinician(
    firstName: "Dr. Sarah"
    lastName: "Smith"
    email: "sarah.smith@hospital.com"
    licenseNumber: "MD12345"
    specialty: "Cardiology"
    phone: "+1234567890"
  ) {
    clinician {
      id
      firstName
      lastName
      specialty
    }
  }
}
```

## Running the Application

1. Install dependencies:
   ```bash
   pip install graphene-django
   ```

2. Run migrations:
   ```bash
   python manage.py migrate
   ```

3. Start the development server:
   ```bash
   python manage.py runserver
   ```

4. Access the GraphQL interface at: http://localhost:8000/graphql/

5. Access Django Admin at: http://localhost:8000/admin/

## Models

### Patient
- Personal information (name, email, phone, DOB)
- Medical record number
- Address and emergency contact
- Linked to Django User model

### Clinician
- Professional information (license, specialty)
- Personal contact details
- Active status
- Linked to Django User model

## Security Notes

- This is a basic implementation for demonstration
- In production, add proper authentication and authorization
- Consider adding rate limiting and input validation
- Database should be properly secured