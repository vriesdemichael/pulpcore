# Generated by Django 2.2.13 on 2020-07-14 21:00

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0040_set_admin_is_staff'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccessPolicy',
            fields=[
                ('pulp_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('pulp_created', models.DateTimeField(auto_now_add=True)),
                ('pulp_last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('statements', django.contrib.postgres.fields.jsonb.JSONField()),
                ('viewset_name', models.CharField(max_length=128, unique=True)),
                ('permissions_assignment', django.contrib.postgres.fields.jsonb.JSONField()),
            ],
            options={
                'abstract': False,
            },
        ),
    ]