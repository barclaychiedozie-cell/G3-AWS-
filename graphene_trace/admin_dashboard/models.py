"""
Admin Dashboard Models
======================
Covers the following admin requirements:

1. Log out                  – handled by Django's built-in auth (no model needed)
2. Manage clinician access  – proxy over ClinicianPatientAccess
3. Assign roles             – proxy over User filtered to role management
4. Create/manage accounts   – proxy over User for full account CRUD
5. Upload patient data      – proxy over PressureUpload for data uploads
"""

from clinicians.models import ClinicianPatientAccess
from patients.models import PressureUpload
from users.models import User


# ── Requirement 2: Manage clinician access to patients ────────────────────────
class ClinicianAccessManagement(ClinicianPatientAccess):
    """
    Proxy model giving admins a dedicated section to manage
    which clinicians can access which patients.
    """
    class Meta:
        proxy = True
        verbose_name = 'Clinician Access'
        verbose_name_plural = 'Manage Clinician Access'


# ── Requirement 3: Assign roles ───────────────────────────────────────────────
class UserRoleAssignment(User):
    """
    Proxy model giving admins a focused view to assign/change
    user roles (admin, clinician, patient).
    """
    class Meta:
        proxy = True
        verbose_name = 'Role Assignment'
        verbose_name_plural = 'Assign User Roles'


# ── Requirement 4: Create and manage user accounts ────────────────────────────
class UserAccountManagement(User):
    """
    Proxy model giving admins full CRUD over user accounts
    (create patients, clinicians, other admins).
    """
    class Meta:
        proxy = True
        verbose_name = 'User Account'
        verbose_name_plural = 'Manage User Accounts'


# ── Requirement 5: Upload patient data ────────────────────────────────────────
class PatientDataUpload(PressureUpload):
    """
    Proxy model giving admins a dedicated section to upload
    pressure data CSV files for patients.
    """
    class Meta:
        proxy = True
        verbose_name = 'Patient Data Upload'
        verbose_name_plural = 'Upload Patient Data'
