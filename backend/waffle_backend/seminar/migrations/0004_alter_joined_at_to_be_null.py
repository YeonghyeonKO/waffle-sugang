# Generated by Django 3.1 on 2020-09-28 05:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seminar', '0003_auto_20200926_1027'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userseminar',
            name='dropped_at',
            field=models.DateTimeField(null=True),
        ),
    ]