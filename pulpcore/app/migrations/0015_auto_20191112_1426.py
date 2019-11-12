# Generated by Django 2.2.6 on 2019-11-12 14:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_remove_repository_plugin_managed'),
    ]

    operations = [
        migrations.RenameField(
            model_name='remote',
            old_name='ssl_ca_certificate',
            new_name='ca_cert',
        ),
        migrations.RenameField(
            model_name='remote',
            old_name='ssl_client_certificate',
            new_name='client_cert',
        ),
        migrations.RenameField(
            model_name='remote',
            old_name='ssl_client_key',
            new_name='client_key',
        ),
        migrations.RenameField(
            model_name='remote',
            old_name='ssl_validation',
            new_name='tls_validation',
        ),
    ]
