# Generated by Django 2.2 on 2020-05-14 04:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scheduling', '0006_auto_20200513_2107'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cams',
            name='flag',
        ),
        migrations.RemoveField(
            model_name='cams',
            name='notes',
        ),
    ]