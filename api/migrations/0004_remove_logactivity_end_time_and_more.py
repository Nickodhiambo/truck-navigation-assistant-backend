# Generated by Django 4.2.7 on 2025-03-29 07:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0003_tripstop_coordinates"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="logactivity",
            name="end_time",
        ),
        migrations.RemoveField(
            model_name="logactivity",
            name="start_time",
        ),
        migrations.AddField(
            model_name="logactivity",
            name="duration",
            field=models.FloatField(default=0.0),
        ),
    ]
