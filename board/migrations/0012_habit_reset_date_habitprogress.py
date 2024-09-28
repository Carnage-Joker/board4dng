# Generated by Django 5.1 on 2024-09-28 14:11

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("board", "0011_alter_familytodoitem_assigned_to"),
    ]

    operations = [
        migrations.AddField(
            model_name="habit",
            name="reset_date",
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.CreateModel(
            name="HabitProgress",
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
                ("date", models.DateField(auto_now_add=True)),
                ("count", models.PositiveIntegerField()),
                (
                    "habit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="progress",
                        to="board.habit",
                    ),
                ),
            ],
        ),
    ]