from django.urls import path

from . import views

urlpatterns = [
    path("marketplace/categories", views.MarketplaceCollectionView.as_view(), {"resource": "categories"}),
    path("marketplace/products", views.MarketplaceCollectionView.as_view(), {"resource": "products"}),
    path("marketplace/products/<slug:product_code>", views.MarketplaceDetailView.as_view()),
    path("marketplace/search", views.MarketplaceCollectionView.as_view(), {"resource": "search"}),
    path("marketplace/publishers", views.MarketplaceCollectionView.as_view(), {"resource": "publishers"}),
    path("marketplace/trial-requests", views.MarketplaceTrialView.as_view()),
    path("marketplace/installation-requests", views.MarketplaceInstallationView.as_view()),
    path("marketplace/update-requests", views.MarketplaceUpdateView.as_view()),
    path("marketplace/rollback-requests", views.MarketplaceRollbackView.as_view()),
    path("marketplace/health", views.PublicConfigView.as_view(), {"resource": "status"}),
    path("sales/discovery", views.SalesDiscoveryView.as_view()),
    path("sales/enrichment", views.SalesEnrichmentView.as_view()),
    path("sales/validation", views.SalesValidationView.as_view()),
    path("sales/research", views.SalesResearchView.as_view()),
    path("sales/scoring", views.SalesScoringView.as_view()),
    path("sales/companies", views.CompanyListView.as_view()),
    path("sales/contacts", views.ContactListView.as_view()),
    path("sales/prospect-lists", views.ProspectListView.as_view()),
    path("sales/crm-submission-requests", views.CrmSubmissionView.as_view()),
    path("sales/health", views.PublicConfigView.as_view(), {"resource": "status"}),
    path("public/site-config", views.PublicConfigView.as_view(), {"resource": "site-config"}),
    path("public/navigation", views.PublicConfigView.as_view(), {"resource": "navigation"}),
    path("public/status", views.PublicConfigView.as_view(), {"resource": "status"}),
]

for form in ("contact", "demo-request", "trial-request", "partner-application", "developer-application", "support-request"):
    urlpatterns.append(path(f"public/{form}", type(f"{form.title()}View", (views.PublicSubmissionView,), {"form_type": form}).as_view()))
