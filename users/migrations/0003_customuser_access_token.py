# Generated by Django 4.2.7 on 2023-11-14 18:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_blacklisttoken'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='access_token',
            field=models.CharField(max_length=108, null=True),
        ),
    ]