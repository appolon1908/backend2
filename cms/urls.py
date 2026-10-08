from .views import (
        LogoViewSet,
        FAQsViewSet, 
        ContactUsViewSet,
        ElectronicBillingInterestViewSet,
        CaseStudyViewSet, 
        TaxPayerViewSet,
        TestimonialViewSet
        )

from .odoo_dashboard import OdooCRMReadViewSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()


router.register(r'case-study', CaseStudyViewSet, basename='case-study')
router.register(r'faqs', FAQsViewSet, basename='faq')
router.register(r'contact-us', ContactUsViewSet, basename='contact-us')
router.register(r'electronic-billing-interest', ElectronicBillingInterestViewSet, basename='electronic-billing-interest')
router.register(r'logo', LogoViewSet, basename='logo')
router.register(r'tax-payer', TaxPayerViewSet, basename='tax-payer')

router.register(r'testimonial', TestimonialViewSet, basename='testimonial')
router.register(r'odoo-crm', OdooCRMReadViewSet, basename='odoo-crm')

urlpatterns = [
    path('', include(router.urls)),
]
