from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models


class Seminar(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    count = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    time = models.TimeField('%H:%M')
    online = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class UserSeminar(models.Model):
    PARTICIPANT = 'participant'
    INSTRUCTOR = 'instructor'

    ROLE_CHOICES = (
        (PARTICIPANT, PARTICIPANT),
        (PARTICIPANT, INSTRUCTOR),
    )

    ROLES = (PARTICIPANT, INSTRUCTOR)

    user = models.ForeignKey(User, related_name='seminars', on_delete=models.CASCADE)
    seminar = models.ForeignKey(Seminar, related_name='users', on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    dropped_at = models.DateTimeField(null=True)

    class Meta:
        unique_together = (
            ('user', 'seminar'),
        )
