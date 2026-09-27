import hashlib
import json
import uuid

from django.db.models import Q
from django.http import JsonResponse
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .gateway import GatewayUnavailable, dispatch, hash_idempotency
from .models import MarketplaceCategory, MarketplaceProduct, MarketplacePublisher, MarketplaceRequest, ProspectList, SalesCompany, SalesContact, SalesJob
from .security import UnsafeTarget, validate_public_url
from .serializers import CategorySerializer, ProductSerializer, ProspectListSerializer, PublisherSerializer, SalesCompanySerializer, SalesContactSerializer

VISIBLE_STATUSES = (MarketplaceProduct.Status.STAGING_VISIBLE, MarketplaceProduct.Status.PRODUCTION_VISIBLE)


def tenant_headers(request):
    values = {
        "Authorization": request.headers.get("Authorization", ""),
        "Idempotency-Key": request.headers.get("Idempotency-Key", "").strip(),
        "X-Tenant-ID": request.headers.get("X-Tenant-ID", "").strip(),
        "X-Workspace-ID": request.headers.get("X-Workspace-ID", "").strip(),
        "X-Audit-Context": request.headers.get("X-Audit-Context", "{}"),
    }
    if not all(values[k] for k in ("Authorization", "Idempotency-Key", "X-Tenant-ID", "X-Workspace-ID")):
        raise ValueError("authorization_tenant_workspace_and_idempotency_required")
    uuid.UUID(values["X-Tenant-ID"]); uuid.UUID(values["X-Workspace-ID"])
    return values


class MarketplaceCollectionView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, resource):
        if resource == "categories": return Response(CategorySerializer(MarketplaceCategory.objects.all().order_by("sort_order"), many=True).data)
        if resource == "publishers": return Response(PublisherSerializer(MarketplacePublisher.objects.filter(status__in=("STAGING_VISIBLE", "PRODUCTION_VISIBLE")), many=True).data)
        products = MarketplaceProduct.objects.filter(status__in=VISIBLE_STATUSES).select_related("publisher", "category")
        if resource == "search":
            q = request.query_params.get("q", "")[:120]
            products = products.filter(Q(display_name__icontains=q) | Q(description__icontains=q) | Q(tags__icontains=q))
            for field in ("language", "support_tier"):
                if request.query_params.get(field): products = products.filter(**{field: request.query_params[field]})
            if request.query_params.get("category"): products = products.filter(category__code=request.query_params["category"])
            if request.query_params.get("publisher"): products = products.filter(publisher__code=request.query_params["publisher"])
            if request.query_params.get("trial_available") in ("true", "false"): products = products.filter(trial_available=request.query_params["trial_available"] == "true")
        try:
            page = max(1, int(request.query_params.get("page", 1)))
            size = min(50, max(1, int(request.query_params.get("page_size", 20))))
        except ValueError:
            return Response({"code": "invalid_pagination"}, status=400)
        total = products.count(); results = products.order_by("display_name")[(page-1)*size:page*size]
        return Response({"count": total, "page": page, "results": ProductSerializer(results, many=True).data})


class MarketplaceDetailView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, product_code):
        product = MarketplaceProduct.objects.filter(product_code=product_code, status__in=VISIBLE_STATUSES).select_related("publisher", "category").first()
        return Response(ProductSerializer(product).data) if product else Response({"code": "not_found"}, status=404)


class GatewayMutationView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "lead_submission"
    kind = ""
    gateway_path = ""
    def post(self, request):
        try: headers = tenant_headers(request)
        except (ValueError, KeyError): return Response({"code": "request_context_required"}, status=400)
        required = ("subscription_reference", "entitlement_reference") if self.kind in ("TRIAL", "INSTALLATION", "UPDATE", "ROLLBACK") else ()
        if any(not request.data.get(k) for k in required): return Response({"code": "subscription_and_entitlement_required"}, status=400)
        try: upstream = dispatch(self.gateway_path, request.data, headers)
        except GatewayUnavailable as exc: return Response({"code": str(exc)}, status=503)
        body = upstream.json() if upstream.content else {"accepted": upstream.ok}
        return Response(body, status=upstream.status_code)


def mutation(kind, path):
    return type(f"{kind.title()}View", (GatewayMutationView,), {"kind": kind, "gateway_path": path})


class SalesDiscoveryView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try: headers = tenant_headers(request); validate_public_url(request.data.get("url", ""))
        except UnsafeTarget as exc: return Response({"code": str(exc)}, status=400)
        except (ValueError, KeyError): return Response({"code": "request_context_required"}, status=400)
        policy = request.data.get("policy", {})
        required = ("timeout_seconds", "rate_limit_per_minute", "max_depth", "max_pages", "max_response_bytes", "retry_limit", "robots_policy", "user_agent")
        if any(k not in policy for k in required): return Response({"code": "bounded_worker_policy_required"}, status=400)
        try: upstream = dispatch("api/v1/sales/discovery", request.data, headers)
        except GatewayUnavailable as exc: return Response({"code": str(exc)}, status=503)
        return Response(upstream.json() if upstream.content else {"accepted": upstream.ok}, status=upstream.status_code)


class TenantListView(APIView):
    permission_classes = [IsAuthenticated]
    model = None; serializer = None
    def get(self, request):
        try: headers = tenant_headers(request)
        except (ValueError, KeyError): return Response({"code": "request_context_required"}, status=400)
        rows = self.model.objects.filter(tenant_id=headers["X-Tenant-ID"], workspace_id=headers["X-Workspace-ID"])
        return Response({"results": self.serializer(rows, many=True).data})


class PublicConfigView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, resource="site-config"):
        payloads = {
            "site-config": {"brand": "Codestra", "locales": ["en", "es", "fr", "ht"], "production_activation": False},
            "navigation": {"items": ["Home", "AI Workforce", "Solutions", "Industries", "Marketplace", "Pricing", "Developers", "Partners", "Academy", "Documentation", "Support", "Company"]},
            "status": {"status": "operational", "detail": "Only approved public service state is shown."},
        }
        return Response(payloads.get(resource, {"code": "not_found"}), status=200 if resource in payloads else 404)


class PublicSubmissionView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]; throttle_scope = "lead_submission"
    form_type = "contact"
    def post(self, request):
        required = ("form_id", "form_version", "submission_id", "timestamp", "source_page", "consent_state", "privacy_policy_version", "idempotency_key")
        if any(not request.data.get(k) for k in required) or request.data.get("website"):
            return Response({"code": "invalid_or_bot_submission"}, status=400)
        headers = {"Authorization": "PublicForm", "Idempotency-Key": request.data["idempotency_key"], "X-Tenant-ID": str(uuid.UUID(int=0)), "X-Workspace-ID": str(uuid.UUID(int=0)), "X-Audit-Context": json.dumps({"form": self.form_type})}
        try: upstream = dispatch(f"api/v1/public/{self.form_type}", request.data, headers)
        except GatewayUnavailable as exc: return Response({"code": str(exc)}, status=503)
        return Response(upstream.json() if upstream.content else {"accepted": upstream.ok}, status=upstream.status_code)


MarketplaceTrialView = mutation("TRIAL", "api/v1/marketplace/trial-requests")
MarketplaceInstallationView = mutation("INSTALLATION", "api/v1/marketplace/installation-requests")
MarketplaceUpdateView = mutation("UPDATE", "api/v1/marketplace/update-requests")
MarketplaceRollbackView = mutation("ROLLBACK", "api/v1/marketplace/rollback-requests")
SalesEnrichmentView = mutation("ENRICHMENT", "api/v1/sales/enrichment")
SalesValidationView = mutation("VALIDATION", "api/v1/sales/validation")
SalesResearchView = mutation("RESEARCH", "api/v1/sales/research")
SalesScoringView = mutation("SCORING", "api/v1/sales/scoring")
CrmSubmissionView = mutation("CRM_SUBMISSION", "api/v1/sales/crm-submission-requests")
CompanyListView = type("CompanyListView", (TenantListView,), {"model": SalesCompany, "serializer": SalesCompanySerializer})
ContactListView = type("ContactListView", (TenantListView,), {"model": SalesContact, "serializer": SalesContactSerializer})
ProspectListView = type("ProspectListView", (TenantListView,), {"model": ProspectList, "serializer": ProspectListSerializer})
