# Generated by Django 4.0.3 on 2022-03-29 17:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scheduling', '0010_alter_course_subject'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cams',
            options={'verbose_name': 'CAMS', 'verbose_name_plural': 'CAMS'},
        ),
        migrations.AlterModelOptions(
            name='schedule',
            options={'ordering': ['term', 'course', 'section']},
        ),
    ]