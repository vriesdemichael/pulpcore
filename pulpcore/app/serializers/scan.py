import shlex
from gettext import gettext as _

from pulpcore.app.serializers import ValidateFieldsMixin
from rest_framework import serializers, fields


def validate_scan_command(scan_command):
    parsed_cmd = shlex.split(scan_command)
    if parsed_cmd:
        return True
    return False


class ScanSerializer(serializers.Serializer, ValidateFieldsMixin):
    scan_command = fields.CharField(
        help_text=_("The command used to scan the artifacts"),
        validators=[validate_scan_command],
        required=True
    )




