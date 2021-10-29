# Generated by Django 3.2.6 on 2021-08-30 11:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0075_rbaccontentguard'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taskreservedresource',
            name='resource',
        ),
        migrations.RemoveField(
            model_name='taskreservedresource',
            name='task',
        ),
        migrations.RemoveField(
            model_name='worker',
            name='cleaned_up',
        ),
        migrations.RemoveField(
            model_name='worker',
            name='gracefully_stopped',
        ),
        migrations.RemoveField(
            model_name='task',
            name='_resource_job_id',
        ),
        migrations.DeleteModel(
            name='ReservedResource',
        ),
        migrations.DeleteModel(
            name='TaskReservedResource',
        ),
    ]
