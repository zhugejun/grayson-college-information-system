# Generated by Django 2.2 on 2020-05-10 19:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scheduling', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='instructor',
            old_name='employeeId',
            new_name='employee_acct',
        ),
    ]
