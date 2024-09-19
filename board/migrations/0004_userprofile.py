# Generated by Django 5.1 on 2024-09-16 02:43

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("board", "0003_user_email_notifications"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserProfile",
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
                ("email_notifications", models.BooleanField(default=True)),
                ("in_app_notifications", models.BooleanField(default=True)),
                (
                    "selected_theme",
                    models.CharField(
                        choices=[
                            ("default", "Default"),
                            ("neon", "Neon"),
                            ("dark", "Dark"),
                            ("blue", "Electric Blue"),
                            ("purple", "Electric Purple"),
                        ],
                        default="default",
                        max_length=20,
                    ),
                ),
                ("privacy_mode", models.BooleanField(default=False)),
                ("message_preview", models.BooleanField(default=True)),
                ("auto_logout", models.BooleanField(default=False)),
                ("location_sharing", models.BooleanField(default=False)),
                ("profile_visibility", models.BooleanField(default=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]