# Generated by Django 4.0.3 on 2022-03-03 17:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduling', '0009_auto_20220106_1320'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='subject',
            field=models.CharField(max_length=4),
        ),
    ]
