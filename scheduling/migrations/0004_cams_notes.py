# Generated by Django 2.2 on 2020-05-13 19:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduling', '0003_cams_flag'),
    ]

    operations = [
        migrations.AddField(
            model_name='cams',
            name='notes',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
