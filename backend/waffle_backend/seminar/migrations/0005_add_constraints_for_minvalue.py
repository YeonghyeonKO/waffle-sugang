# Generated by Django 3.1 on 2020-11-09 08:57

from django.conf import settings
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('seminar', '0004_alter_joined_at_to_be_null'),
    ]

    operations = [
        migrations.AlterField(
            model_name='seminar',
            name='capacity',
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AlterField(
            model_name='seminar',
            name='count',
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AlterField(
            model_name='seminar',
            name='name',
            field=models.CharField(db_index=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='userseminar',
            name='role',
            field=models.CharField(db_index=True, max_length=50),
        ),
        migrations.AlterUniqueTogether(
            name='userseminar',
            unique_together={('user', 'seminar')},
        ),
    ]