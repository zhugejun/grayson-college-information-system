# Generated by Django 2.2 on 2020-05-13 21:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scheduling', '0005_auto_20200513_2104'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schedule',
            name='instructor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='scheduling.Instructor'),
        ),
    ]
