from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User


def _format_id(role: str, pk: int) -> str:
    prefix = "PAT" if role == "patient" else "CLI"
    return f"{prefix}-{pk:07d}"


@receiver(post_save, sender=User)
def assign_id_number(sender, instance: User, created: bool, **kwargs):
    if not created:
        return

    if instance.id_number:
        return

    # pk exists after the first save, so we update it once here
    id_number = _format_id(instance.role, instance.pk)
    User.objects.filter(pk=instance.pk).update(id_number=id_number)