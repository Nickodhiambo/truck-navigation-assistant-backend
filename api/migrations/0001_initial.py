# Generated by Django 4.2.7 on 2025-03-23 12:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Trip",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("pickup_location", models.CharField(max_length=255)),
                ("dropoff_location", models.CharField(max_length=255)),
                ("distance", models.FloatField(help_text="Distance in miles")),
                (
                    "estimated_hours",
                    models.FloatField(help_text="Estimated driving hours"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("SCHEDULED", "scheduled"),
                            ("ACTIVE", "active"),
                            ("COMPLETED", "completed"),
                            ("CANCELlED", "cancelled"),
                        ],
                        default="SCHEDULED",
                        max_length=20,
                    ),
                ),
                ("start_time", models.DateTimeField(blank=True, null=True)),
                ("end_time", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "driver",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="trips",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="TripStop",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "stop_type",
                    models.CharField(
                        choices=[
                            ("pickup", "Pickup"),
                            ("dropoff", "Dropoff"),
                            ("rest", "Rest Stop"),
                            ("fuel", "Rest fuel"),
                        ],
                        max_length=10,
                    ),
                ),
                ("location", models.CharField(max_length=255)),
                ("arrival_time", models.CharField(max_length=50)),
                ("duration", models.FloatField(help_text="Duration in hrs")),
                (
                    "trip",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="stop",
                        to="api.trip",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="LogSheet",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateField()),
                (
                    "hours_logged",
                    models.FloatField(help_text="Total hours logged for this day"),
                ),
                ("cycle_hours", models.FloatField(help_text="Accumilated cycle hours")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("DRAFT", "Draft"),
                            ("SUBMITTED", "submitted"),
                            ("APPROVED", "approved"),
                        ],
                        default="DRAFT",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "driver",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="log_sheets",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "trip",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="log_sheets",
                        to="api.trip",
                    ),
                ),
            ],
            options={
                "unique_together": {("driver", "date")},
            },
        ),
        migrations.CreateModel(
            name="LogActivity",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "activity_type",
                    models.CharField(
                        choices=[
                            ("Driving", "Driving"),
                            ("ON_DUTY", "On Duty Not Driving"),
                            ("OFF_DUTY", "Off duty"),
                            ("SLEEPER", "Sleeper Bearth"),
                        ],
                        max_length=20,
                    ),
                ),
                ("start_time", models.CharField(max_length=10)),
                ("end_time", models.CharField(max_length=10)),
                ("description", models.CharField(max_length=255)),
                ("location", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "log_sheet",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="activities",
                        to="api.logsheet",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="HoursOfService",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateField()),
                (
                    "cycle_used",
                    models.FloatField(
                        default=0.0, help_text="Hours used in 70-hr/8 days cycle"
                    ),
                ),
                (
                    "daily_used",
                    models.FloatField(
                        default=0.0, help_text="Hours used in 14-hr daily window"
                    ),
                ),
                (
                    "driving_used",
                    models.FloatField(
                        default=0.0, help_text="Hours used in 11-hr driving limit"
                    ),
                ),
                (
                    "driver",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="hours_of_service",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "unique_together": {("driver", "date")},
            },
        ),
    ]
