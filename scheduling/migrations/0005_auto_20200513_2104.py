# Generated by Django 2.2 on 2020-05-13 21:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scheduling', '0004_cams_notes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cams',
            name='instructor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='scheduling.Instructor'),
        ),
    ]
