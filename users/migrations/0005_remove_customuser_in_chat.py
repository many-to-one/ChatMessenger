# Generated by Django 4.2.7 on 2023-12-06 17:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_customuser_in_chat'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='in_chat',
        ),
    ]
