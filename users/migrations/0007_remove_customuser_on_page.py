# Generated by Django 4.2.7 on 2023-12-09 20:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_customuser_on_page'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='on_page',
        ),
    ]
