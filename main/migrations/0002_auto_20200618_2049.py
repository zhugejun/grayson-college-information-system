# Generated by Django 2.2.13 on 2020-06-18 20:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='subjects',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]