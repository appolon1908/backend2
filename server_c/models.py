import uuid

from django.db import models


class TenantRecord(models.Model):
    tenant_id = models.UUIDField(db_index=True)
    workspace_id = models.UUIDField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class MarketplacePublisher(models.Model):
    code = models.SlugField(max_length=80, unique=True)
    display_name = models.CharField(max_length=160)
    status = models.CharField(max_length=32, default="DRAFT", db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class MarketplaceCategory(models.Model):
    code = models.CharField(max_length=40, unique=True)
    display_name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)


class MarketplaceProduct(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT"
        VALIDATING = "VALIDATING"
        SECURITY_REVIEW = "SECURITY_REVIEW"
        BUSINESS_REVIEW = "BUSINESS_REVIEW"
        APPROVED_FOR_STAGING = "APPROVED_FOR_STAGING"
        STAGING_VISIBLE = "STAGING_VISIBLE"
        PAUSED = "PAUSED"
        DEPRECATED = "DEPRECATED"
        RETIRED = "RETIRED"
        APPROVED_FOR_PRODUCTION_REVIEW = "APPROVED_FOR_PRODUCTION_REVIEW"
        PRODUCTION_VISIBLE = "PRODUCTION_VISIBLE"

    product_code = models.SlugField(max_length=100, unique=True)
    display_name = models.CharField(max_length=180)
    publisher = models.ForeignKey(MarketplacePublisher, on_delete=models.PROTECT)
    category = models.ForeignKey(MarketplaceCategory, on_delete=models.PROTECT)
    description = models.TextField()
    supported_industries = models.JSONField(default=list)
    supported_platform_versions = models.JSONField(default=list)
    required_permissions = models.JSONField(default=list)
    required_capabilities = models.JSONField(default=list)
    required_connectors = models.JSONField(default=list)
    installation_scope = models.CharField(max_length=40, default="STAGING")
    risk_level = models.CharField(max_length=20, default="MEDIUM")
    trial_available = models.BooleanField(default=False)
    documentation_reference = models.URLField(blank=True)
    support_reference = models.URLField(blank=True)
    status = models.CharField(max_length=40, choices=Status.choices, default=Status.DRAFT, db_index=True)
    version = models.CharField(max_length=40)
    language = models.CharField(max_length=12, default="en")
    tags = models.JSONField(default=list)
    pricing_reference = models.CharField(max_length=120, blank=True)
    support_tier = models.CharField(max_length=40, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class MarketplacePackage(models.Model):
    package_code = models.SlugField(max_length=100)
    package_version = models.CharField(max_length=40)
    product = models.ForeignKey(MarketplaceProduct, on_delete=models.CASCADE, related_name="packages")
    manifest = models.JSONField(default=dict)
    checksum = models.CharField(max_length=128)
    signature_reference = models.CharField(max_length=300)
    rollback_version = models.CharField(max_length=40)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["package_code", "package_version"], name="unique_marketplace_package_version")]


class MarketplaceRequest(TenantRecord):
    class Kind(models.TextChoices):
        TRIAL = "TRIAL"
        INSTALLATION = "INSTALLATION"
        UPDATE = "UPDATE"
        ROLLBACK = "ROLLBACK"

    request_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    product_code = models.CharField(max_length=100)
    package_version = models.CharField(max_length=40, blank=True)
    subscription_reference = models.CharField(max_length=120)
    entitlement_reference = models.CharField(max_length=120)
    approval_reference = models.CharField(max_length=120, blank=True)
    idempotency_key_hash = models.CharField(max_length=64, unique=True)
    middleware_reference = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=32, default="PENDING_MIDDLEWARE")
    audit_context = models.JSONField(default=dict)


class SalesCompany(TenantRecord):
    company_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=200)
    normalized_domain = models.CharField(max_length=253, db_index=True)
    industry = models.CharField(max_length=120, blank=True)
    source_url = models.URLField(max_length=1000)
    source_timestamp = models.DateTimeField()
    verification_state = models.CharField(max_length=24, default="UNVERIFIED")
    enrichment = models.JSONField(default=dict)


class SalesContact(TenantRecord):
    contact_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    company = models.ForeignKey(SalesCompany, on_delete=models.CASCADE, related_name="contacts")
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=160, blank=True)
    email_candidate = models.EmailField(blank=True)
    phone_candidate = models.CharField(max_length=40, blank=True)
    confidence = models.DecimalField(max_digits=4, decimal_places=3, default=0)
    verification_state = models.CharField(max_length=24, default="UNVERIFIED")
    source = models.URLField(max_length=1000)


class SalesJob(TenantRecord):
    job_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    kind = models.CharField(max_length=32)
    status = models.CharField(max_length=32, default="QUEUED")
    policy = models.JSONField(default=dict)
    request = models.JSONField(default=dict)
    result = models.JSONField(default=dict)
    idempotency_key_hash = models.CharField(max_length=64, unique=True)
    middleware_reference = models.CharField(max_length=160, blank=True)


class ProspectList(TenantRecord):
    list_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    owner = models.CharField(max_length=160)
    purpose = models.CharField(max_length=240)
    industry = models.CharField(max_length=120, blank=True)
    geography = models.JSONField(default=list)
    minimum_score = models.PositiveSmallIntegerField(default=0)
    required_verification = models.CharField(max_length=24, default="VERIFIED")
    suppression_policy = models.JSONField(default=dict)
    expiration = models.DateTimeField()
    status = models.CharField(max_length=32, default="DRAFT")


class ServerCAuditEvent(TenantRecord):
    event_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    event_type = models.CharField(max_length=100, db_index=True)
    actor_reference = models.CharField(max_length=160)
    resource_reference = models.CharField(max_length=200)
    metadata = models.JSONField(default=dict)
