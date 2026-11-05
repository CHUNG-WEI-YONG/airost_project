from django.db import models
from django.conf import settings

# Create your models here.

class Club(models.Model):
    name=models.CharField(max_length=255)
    description=models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Membership(models.Model):
    class Role(models.TextChoices):
        PRESIDENT='president','President'
        TREASURER='treasurer', 'Treasurer'
        MEMBER='member','Member'

    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="club_memberships",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["club", "user"],
                name="one_membership_per_club_user",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.club} {self.role}"
