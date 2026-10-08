from django.conf import settings
from rest_framework.viewsets import ViewSet, ModelViewSet
from .models import (
            FAQs, 
            Logo, 
            TaxPayer,
            CaseStudy, 
            ContactUs, 
            ElectronicBillingInterest,
            Testimonial,
            HeaderTitle, 
            TaxPayerMedia,
            )
from .serializers import (
            FaqSerializer, 
            LogoSerializer, 
            TaxPayerSerializer,
            CaseStudySerializer, 
            ContactUsSerializer, 
            ElectronicBillingInterestSerializer,
            TestimonialSerializer,
            HeaderTitleSerializer, 
            )
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from django.db import transaction

from notification.service import EmailService

from rest_framework.decorators import action
from .odoo import sync_billing_interest, sync_contact, sync_taxpayer
     


class CaseStudyViewSet(ViewSet):

    def get_queryset(self):
        return CaseStudy.objects.all()

    @swagger_auto_schema(
        operation_description="List all Case Study",
        operation_summary="List all Case Study",
        tags=["CaseStudy"],
    )
    def list(self, request):
        queryset = self.get_queryset()
        serializer = CaseStudySerializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Case Study Form",
        operation_summary="Case Study Form",
        tags=["CaseStudy"],
        request_body=CaseStudySerializer
    )
    def create(self, request):
        serializer = CaseStudySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Get a single Case Study",
        operation_summary="Get a single Case Study",
        tags=["CaseStudy"],
    )
    def retrieve(self, request, pk=None):
        try:
            case_study = CaseStudy.objects.get(pk=pk)
        except CaseStudy.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = CaseStudySerializer(case_study)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Update Case Study",
        operation_summary="Update Case Study",
        tags=["CaseStudy"],
        request_body=CaseStudySerializer
    )
    def update(self, request, pk=None):
        try:
            case_study = CaseStudy.objects.get(pk=pk)
        except CaseStudy.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = CaseStudySerializer(case_study, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete Case Study",
        operation_summary="Delete Case Study",
        tags=["CaseStudy"],
    )
    def destroy(self, request, pk=None):
        try:
            case_study = CaseStudy.objects.get(pk=pk)
        except CaseStudy.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        case_study.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @swagger_auto_schema(
        operation_description="Get Hero header title for case-study page",
        operation_summary="Get Hero header title for case-study page",
        tags=["CaseStudy"],
    )
    @action(detail=False, methods=['get'], url_path="hero/header-title/get")
    def get_blog_header_title(self, request):
        header_title = HeaderTitle.objects.filter(page='case_study').order_by('-created_at').first()
        
        if not header_title:
            return Response({'message': 'No header title found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(HeaderTitleSerializer(header_title).data, status=status.HTTP_200_OK)
    

    @swagger_auto_schema(
        operation_description="Create Hero Header Title for Case Study page",
        operation_summary="Create Hero Header Title for Case Study page",
        tags=["CaseStudy"],
        request_body=HeaderTitleSerializer
    )
    @action(detail=False, methods=['post'], url_path="hero/header-title")
    def create_blog_header_title(self, request):
        serializer = HeaderTitleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(page='case_study')
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FAQsViewSet(ViewSet):
    

    def get_queryset(self):
        return FAQs.objects.all()

    @swagger_auto_schema(
        operation_description="FAQs",
        operation_summary="FAQs",
        tags=["FAQs"],
    )
    def list(self, request):
        queryset = self.get_queryset()
        serializer = FaqSerializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="FAQs form",
        operation_summary="FAQs form",
        tags=["FAQs"],
        request_body=FaqSerializer
    )
    def create(self, request):
        serializer = FaqSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    




    @swagger_auto_schema(
        operation_description="Retrieve FAQs",
        operation_summary="Retrieve FAQs",
        tags=["FAQs"],
    )
    def retrieve(self, request, pk=None):
        try:
            faq = FAQs.objects.get(pk=pk)
        except FAQs.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = FaqSerializer(faq)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Update FAQs",
        operation_summary="Update FAQs",
        tags=["FAQs"],
    )
    def update(self, request, pk=None):
        try:
            faq = FAQs.objects.get(pk=pk)
        except FAQs.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = FaqSerializer(faq, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete FAQs",
        operation_summary="Delete FAQs",
        tags=["FAQs"],
    )
    def destroy(self, request, pk=None):
        try:
            faq = FAQs.objects.get(pk=pk)
        except FAQs.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        faq.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class ContactUsViewSet(ViewSet):
    def get_permissions(self):
        return [AllowAny()] if self.action == 'create' else [IsAdminUser()]
    
    def list(self, request):
        return Response(ContactUsSerializer(ContactUs.objects.all(), many=True).data)
    
    @swagger_auto_schema(
        operation_description="Contact Us form",
        operation_summary="Contact Us form",
        tags=["contact-us"],
        request_body=ContactUsSerializer
    )
    def create(self, request):
        serializer = ContactUsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        contact = serializer.save()
        sync_contact(contact)
        
        # send email to our mail address
        EmailService.send_async(
            template="contact_us.html",
            subject="Contact Us Request",
            recipients=[settings.ADMIN_EMAIL],
            context={
                "full_name": serializer.validated_data.get('full_name'),
                "email": serializer.validated_data.get('email'),
                "company_size": serializer.validated_data.get('company_size'),
                "message": serializer.validated_data.get('message'),
            }
        )
        
        return Response({"message": "Thank you for contacting us"}, status=status.HTTP_201_CREATED)


class ElectronicBillingInterestViewSet(ViewSet):
    def get_permissions(self):
        return [AllowAny()] if self.action == "create" else [IsAdminUser()]

    @swagger_auto_schema(
        operation_description="Electronic billing consultation form",
        operation_summary="Request an electronic billing consultation",
        tags=["electronic-billing"],
        request_body=ElectronicBillingInterestSerializer,
    )
    def create(self, request):
        serializer = ElectronicBillingInterestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        interest = serializer.save()
        sync_billing_interest(interest)
        return Response(
            {"message": "Thank you. A Codestra specialist will contact you."},
            status=status.HTTP_201_CREATED,
        )
    
    @swagger_auto_schema(
        operation_description="Contact Us",
        operation_summary="Contact Us",
        tags=["contact-us"],
    )
    def list(self, request):
        queryset = ElectronicBillingInterest.objects.all()
        serializer = ElectronicBillingInterestSerializer(queryset, many=True)
        return Response(serializer.data)
    
    

class LogoViewSet(ViewSet):
    def get_queryset(self):
        return Logo.objects.all().order_by('-created_at')
    
    
    @swagger_auto_schema(
        operation_description="Home page logo",
        operation_summary="Home page logo",
        tags=["home-page-logo"],
    )
    def list(self, request):
        queryset = self.get_queryset()
        serializer = LogoSerializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Home page logo form",
        operation_summary="Home page logo form",
        tags=["home-page-logo"],
        request_body=LogoSerializer
    )
    def create(self, request):
        serializer = LogoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Home page logo",
        operation_summary="Home page logo",
        tags=["home-page-logo"],
    )
    def retrieve(self, request, pk=None):
        try:
            logo = Logo.objects.get(pk=pk)
        except Logo.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = LogoSerializer(logo)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Home page logo",
        operation_summary="Home page logo",
        tags=["home-page-logo"],
    )
    def update(self, request, pk=None):
        try:
            logo = Logo.objects.get(pk=pk)
        except Logo.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = LogoSerializer(logo, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Home page logo",
        operation_summary="Home page logo",
        tags=["home-page-logo"],
    )
    def destroy(self, request, pk=None):
        try:
            logo = Logo.objects.get(pk=pk)
        except Logo.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        logo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class TaxPayerViewSet(ViewSet):
    def get_permissions(self):
        return [AllowAny()] if self.action == 'create' else [IsAdminUser()]


    # Effect-capable CRM writes are submitted through Middleware in cms.odoo.
     

    #endpoints
    def get_queryset(self):
        return TaxPayer.objects.all()

    @swagger_auto_schema(
        operation_description="List Taxpayers registration",
        operation_summary="List Taxpayers registration",
        tags=["tax-payer"],
    )
    def list(self, request):
        queryset = self.get_queryset()
        serializer = TaxPayerSerializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Taxpayer registration form",
        operation_summary="Taxpayer registration form",
        tags=["tax-payer"],
        request_body=TaxPayerSerializer
    )
    def create(self, request):

        # files = request.FILES.getlist('media_files')
        # serializer = TaxPayerSerializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        # taxpayer = serializer.save()
        
        # if len(files) > 5:
        #     return Response({"error": "You can only upload a maximum of 5 files"}, status=status.HTTP_400_BAD_REQUEST)
        
        # media_objects = [
        #     TaxPayerMedia(taxpayer=taxpayer, media_file=file) for file in files
        # ]
        # TaxPayerMedia.objects.bulk_create(media_objects)
        # return Response(serializer.data, status=status.HTTP_201_CREATED)


        files = request.FILES.getlist('media_files')
        serializer = TaxPayerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if len(files) > 5:
            return Response({"error": "You can only upload a maximum of 5 files"}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            taxpayer = serializer.save()
            TaxPayerMedia.objects.bulk_create([
                TaxPayerMedia(taxpayer=taxpayer, media_file=file) for file in files
            ])
        sync_taxpayer(taxpayer)
        return Response({"form_data": TaxPayerSerializer(taxpayer).data}, status=status.HTTP_201_CREATED)


    @swagger_auto_schema(
        operation_description="Retrieve Taxpayer",
        operation_summary="Retrieve Taxpayer",
        tags=["tax-payer"],
    )
    def retrieve(self, request, pk=None):
        try:
            taxpayer = TaxPayer.objects.get(pk=pk)
        except TaxPayer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = TaxPayerSerializer(taxpayer)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Update Taxpayer",
        operation_summary="Update Taxpayer",
        tags=["tax-payer"],
        request_body=TaxPayerSerializer
    )
    def update(self, request, pk=None):
        # try:
        #     taxpayer = TaxPayer.objects.get(pk=pk)
        # except TaxPayer.DoesNotExist:
        #     return Response(status=status.HTTP_404_NOT_FOUND)
        # serializer = TaxPayerSerializer(taxpayer, data=request.data)
        # if serializer.is_valid():
        #     serializer.save()
        #     return Response(serializer.data)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

           # taxpayer = TaxPayer.objects.get(pk=pk)
       # except TaxPayer.DoesNotExist:
            #return Response(status=status.HTTP_404_NOT_FOUND)
            
            try:
                taxpayer = TaxPayer.objects.get(pk=pk)
            except TaxPayer.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = TaxPayerSerializer(taxpayer, data=request.data)
            serializer.is_valid(raise_exception=True)
            taxpayer = serializer.save(odoo_sync_status="pending")
            sync_taxpayer(taxpayer)
            return Response({"form_data": serializer.data}, status=status.HTTP_200_OK)


    

    @swagger_auto_schema(
        operation_description="Delete Taxpayer",
        operation_summary="Delete Taxpayer",
        tags=["tax-payer"],
        request_body=TaxPayerSerializer
    )
    def destroy(self, request, pk=None):
        try:
            taxpayer = TaxPayer.objects.get(pk=pk)
        except TaxPayer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        taxpayer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    


     

class TestimonialViewSet(ViewSet):
    # serializer_class = TestimonialSerializer
    
    def get_queryset(self):
        return Testimonial.objects.all()

    @swagger_auto_schema(
        operation_description="List all Testimonials",
        operation_summary="List all Testimonials",
        tags=["Testimonial"],
    )
    def list(self, request):
        queryset = self.get_queryset()
        serializer = TestimonialSerializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create a Testimonial",
        operation_summary="Create a Testimonial",
        tags=["Testimonial"],
        request_body=TestimonialSerializer
    )
    def create(self, request):
        serializer = TestimonialSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Retrieve a Testimonial",
        operation_summary="Retrieve a Testimonial",
        tags=["Testimonial"],
    )
    def retrieve(self, request, pk=None):
        try:
            testimonial = Testimonial.objects.get(pk=pk)
        except Testimonial.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = TestimonialSerializer(testimonial)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Update a Testimonial",
        operation_summary="Update a Testimonial",
        tags=["Testimonial"],
        request_body=TestimonialSerializer
    )
    def update(self, request, pk=None):
        try:
            testimonial = Testimonial.objects.get(pk=pk)
        except Testimonial.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = TestimonialSerializer(testimonial, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete a Testimonial",
        operation_summary="Delete a Testimonial",
        tags=["Testimonial"],
    )
    def destroy(self, request, pk=None):
        try:
            testimonial = Testimonial.objects.get(pk=pk)
        except Testimonial.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        testimonial.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
