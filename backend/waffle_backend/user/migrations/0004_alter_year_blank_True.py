# Generated by Django 3.1 on 2020-09-28 14:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_alter_ParticipantProfile_field_seminar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instructorprofile',
            name='year',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
