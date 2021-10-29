import logging

from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView

from pulpcore.app.response import OperationPostponedResponse
from pulpcore.app.serializers import AsyncOperationResponseSerializer, RepairSerializer
from pulpcore.app.serializers.scan import ScanSerializer
from pulpcore.app.tasks import scan_all_artifacts
from pulpcore.tasking.tasks import dispatch


class ScanView(APIView):
    @extend_schema(
        description=(
                "Trigger an asynchronous task that scans all known artifacts"
        ),
        request=ScanSerializer,
        summary="Scan stored artifacts",
        responses={202: AsyncOperationResponseSerializer},

    )
    def post(self, request):
        """
        Repair artifacts.
        """

        serializer = ScanSerializer(data=request.data)
        serializer.is_valid()

        log = logging.getLogger(__name__)
        log.info("DEBUG serializer_data %s", serializer.validated_data)

        scan_command = serializer.validated_data["scan_command"]

        task = dispatch(scan_all_artifacts, [], args=(scan_command,))

        return OperationPostponedResponse(task, request)
