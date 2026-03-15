import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User
from django.db import models
from .models import Patient, Clinician
from graphene import relay


class PatientType(DjangoObjectType):
    age = graphene.Int()

    class Meta:
        model = Patient
        fields = ('id', 'user', 'first_name', 'last_name', 'email', 'phone', 'date_of_birth',
                 'medical_record_number', 'address', 'emergency_contact_name',
                 'emergency_contact_phone', 'created_at', 'updated_at')

    def resolve_age(self, info):
        return self.age


class ClinicianType(DjangoObjectType):
    class Meta:
        model = Clinician
        fields = ('id', 'user', 'first_name', 'last_name', 'email', 'phone', 'license_number',
                 'specialty', 'is_active', 'created_at', 'updated_at')


class CreatePatient(graphene.Mutation):
    class Arguments:
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()
        date_of_birth = graphene.Date(required=True)
        medical_record_number = graphene.String(required=True)
        address = graphene.String()
        emergency_contact_name = graphene.String()
        emergency_contact_phone = graphene.String()

    patient = graphene.Field(PatientType)

    @classmethod
    def mutate(cls, root, info, first_name, last_name, email, date_of_birth,
               medical_record_number, phone="", address="", emergency_contact_name="",
               emergency_contact_phone=""):
        # Create a Django user for the patient
        username = f"{first_name.lower()}.{last_name.lower()}.{medical_record_number}"
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name
        )

        patient = Patient.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            date_of_birth=date_of_birth,
            medical_record_number=medical_record_number,
            address=address,
            emergency_contact_name=emergency_contact_name,
            emergency_contact_phone=emergency_contact_phone
        )

        return CreatePatient(patient=patient)


class CreateClinician(graphene.Mutation):
    class Arguments:
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()
        license_number = graphene.String(required=True)
        specialty = graphene.String(required=True)

    clinician = graphene.Field(ClinicianType)

    @classmethod
    def mutate(cls, root, info, first_name, last_name, email, license_number,
               specialty, phone=""):
        # Create a Django user for the clinician
        username = f"dr.{first_name.lower()}.{last_name.lower()}"
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name
        )

        clinician = Clinician.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            license_number=license_number,
            specialty=specialty
        )

        return CreateClinician(clinician=clinician)


class Query(graphene.ObjectType):
    # Patient queries
    patients = graphene.List(PatientType, search=graphene.String(), limit=graphene.Int(), offset=graphene.Int())
    patient = graphene.Field(PatientType, id=graphene.ID(required=True))
    patient_count = graphene.Int()

    # Clinician queries
    clinicians = graphene.List(ClinicianType, specialty=graphene.String())
    clinician = graphene.Field(ClinicianType, id=graphene.ID(required=True))

    def resolve_patients(self, info, search=None, limit=None, offset=None):
        queryset = Patient.objects.all()

        if search:
            queryset = queryset.filter(
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(medical_record_number__icontains=search)
            )

        if offset:
            queryset = queryset[offset:]

        if limit:
            queryset = queryset[:limit]

        return queryset

    def resolve_patient(self, info, id):
        try:
            return Patient.objects.get(id=id)
        except Patient.DoesNotExist:
            return None

    def resolve_patient_count(self, info):
        return Patient.objects.count()

    def resolve_clinicians(self, info, specialty=None):
        queryset = Clinician.objects.filter(is_active=True)
        if specialty:
            queryset = queryset.filter(specialty__icontains=specialty)
        return queryset

    def resolve_clinician(self, info, id):
        try:
            return Clinician.objects.get(id=id, is_active=True)
        except Clinician.DoesNotExist:
            return None


class Mutation(graphene.ObjectType):
    create_patient = CreatePatient.Field()
    create_clinician = CreateClinician.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)