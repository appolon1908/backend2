from .views import (
        LogoViewSet,
        FAQsViewSet, 
        ContactUsViewSet,
        CaseStudyViewSet, 
        TaxPayerViewSet,
        TestimonialViewSet
        )

from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()


router.register(r'case-study', CaseStudyViewSet, basename='case-study')
router.register(r'faqs', FAQsViewSet, basename='faq')
router.register(r'contact-us', ContactUsViewSet, basename='contact-us')
router.register(r'logo', LogoViewSet, basename='logo')
router.register(r'tax-payer', TaxPayerViewSet, basename='tax-payer')

router.register(r'testimonial', TestimonialViewSet, basename='testimonial')

urlpatterns = [
    path('', include(router.urls)),
]