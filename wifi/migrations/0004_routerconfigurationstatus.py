# Generated by Django 5.1.3 on 2024-11-18 08:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wifi', '0003_package_minutes_limit'),
    ]

    operations = [
        migrations.CreateModel(
            name='RouterConfigurationStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
