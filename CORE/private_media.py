"""Authenticated access to uploaded tax and application documents."""
from pathlib import PurePosixPath

from django.db.models import Q
from django.http import FileResponse, Http404
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView

from career_app.models import CareerApplication
from cms.models import TaxPayerMedia


class PrivateDocumentView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, category, filename):
        # A request can name only a file already attached to the matching model.
        parts = PurePosixPath(filename).parts
        if not parts or ".." in parts or "\\" in filename or filename.startswith("/"):
            raise Http404
        if category == "tax":
            name = f"tax/images/{filename}"
            record = TaxPayerMedia.objects.filter(media_file=name).first()
            field = record.media_file if record else None
        else:
            name = f"career/{filename}"
            record = CareerApplication.objects.filter(Q(resume=name) | Q(user_id=name)).first()
            field = (record.resume if record.resume.name == name else record.user_id) if record else None
        if not field:
            raise Http404
        try:
            response = FileResponse(field.open("rb"), as_attachment=True, filename=PurePosixPath(field.name).name)
        except (OSError, ValueError):
            raise Http404
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response
