from django.conf import settings
from rest_framework.viewsets import ViewSet, ModelViewSet
from .models import (
            FAQs, 
            Logo, 
            TaxPayer,
            CaseStudy, 
            ContactUs, 
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
            TestimonialSerializer,
            HeaderTitleSerializer, 
            )
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from django.db import transaction

from notification.service import EmailService

from rest_framework.decorators import action
import requests
     


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
        return [AllowAny()] if self.action == 'create' else super().get_permissions()
    
    def get_queryset(self):
        return super().get_queryset()
    
    #Part to odoo
    def send_to_odoo(self, data):
        odoo_url = f'{settings.ODOO_BASE_URL}/crm/lead/create'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.ODOO_API_TOKEN}'
        }

        
        odoo_data = {
            "full_name": data.get("full_name"),
            "email": data.get("email"),
            "company_size": data.get("company_size"),
            "message": data.get("message"),
            
        }

        try:
            response = requests.post(odoo_url, headers=headers, json=odoo_data, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error sending data to Odoo: {response.status_code} - {response.text}")
                return {"error": f"Error sending data to Odoo: {response.status_code} - {response.text}"}

        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Odoo: {e}")
            return {"error": f"Error connecting to Odoo: {e}"}
    

    @swagger_auto_schema(
        operation_description="Contact Us form",
        operation_summary="Contact Us form",
        tags=["contact-us"],
        request_body=ContactUsSerializer
    )
    def create(self, request):
        serializer = ContactUsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        contact = ContactUs.objects.create(
            **serializer.validated_data
        )

        odoo_response = self.send_to_odoo(request.data)

        if "error" in odoo_response:
            return Response({
                "message": "Thank you for contacting us. However, there was an issue sending your request to Odoo.",
                "odoo_error": odoo_response
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
    
    @swagger_auto_schema(
        operation_description="Contact Us",
        operation_summary="Contact Us",
        tags=["contact-us"],
    )
    def list(self, request):
        queryset = ContactUs.objects.all()
        serializer = ContactUsSerializer(queryset, many=True)
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
        return [AllowAny()] if self.action == 'create' else super().get_permissions()


    #Sent taxpayer form to odoo funtion:
    def send_to_odoo(self, request, data):
        """
        This function is responsible for sending the data to Odoo after the taxpayer is created.
        It receives the JSON directly from the request and processes it.
        """
        odoo_url = f'{settings.ODOO_BASE_URL}/contribuyente/register'
    
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.ODOO_API_TOKEN}'
        }
    
        #Send data to Odoo in JSON format
        odoo_data = {
            "taxpayer_rnc": data.get("tax_payer_rnc"),
            "taxpayer_name": data.get("name_of_tax_payer"),
            "trade_name": data.get("trade_name"),
            "taxpayer_telephone": data.get("tax_payer_telephone"),
            "taxpayer_cell_phone": data.get("tax_payer_cell_phone"),
            "taxpayer_email": data.get("tax_payer_email"),
            "taxpayer_number": data.get("tax_payer_number"),
            "taxpayer_sector": data.get("tax_payer_sector"),
            "taxpayer_province": data.get("tax_payer_province"),
            "address_reference": data.get("address_reference"),
            "visiting_hours": data.get("visiting_hours"),
            "representation_rnc": data.get("representation_rnc"),
            "name_of_representative": data.get("name_of_representative"),
            "representative_phone": data.get("representative_phone"),
            "representative_cell_phone": data.get("representative_cell_phone"),
            "representative_email": data.get("representative_email"),
            "street_of_warehouse": data.get("street_of_warehouse"),
            "store_or_warehouse_number": data.get("store_or_warehouse_number"),
            "province_of_warehouse": data.get("province_of_warehouse"),
            "warehouse_reference": data.get("warehouse_reference"),
            "local_administration": data.get("local_administration"),
            "warehouse_sector": data.get("warehouse_sector"),
            "operation_carried_out_in_premise": data.get("operation_carried_out_in_premise"),
    
            #If the media file is present, use the URL
            "media_file": data.get("media_file") if data.get("media_file") else None,
            #"odoo_id": request.user.odoo_id
        }
    
       
        try:
            response = requests.post(odoo_url, headers=headers, json=odoo_data, timeout=10)
            
            if response.status_code == 200:
              
                return response.json()
            else:
                
                print(f"Error in Odoo. Status Code: {response.status_code}, Mensaje: {response.text}")
                raise Exception(f"Error sending data to Odoo: {response.text}")
        
        except requests.exceptions.RequestException as e:
            
            print(f"Error sending data to Odoo: {str(e)}")
            raise Exception(f"Odoo connection error: {str(e)}")
    
    #to update.
    def send_update_to_odoo(self, request, data):
        
        """
        This feature sends the updated data to Odoo.
        """
        odoo_url = f'{settings.ODOO_BASE_URL}/contribuyente/register'

        headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {settings.ODOO_API_TOKEN}'
        }

        
        odoo_data = {
        "taxpayer_rnc": data.get("tax_payer_rnc"),
        "taxpayer_name": data.get("name_of_tax_payer"),
        "trade_name": data.get("trade_name"),
        "taxpayer_telephone": data.get("tax_payer_telephone"),
        "taxpayer_cell_phone": data.get("tax_payer_cell_phone"),
        "taxpayer_email": data.get("tax_payer_email"),
        "taxpayer_number": data.get("tax_payer_number"),
        "taxpayer_sector": data.get("tax_payer_sector"),
        "taxpayer_province": data.get("tax_payer_province"),
        "address_reference": data.get("address_reference"),
        "visiting_hours": data.get("visiting_hours"),
        "representation_rnc": data.get("representation_rnc"),
        "name_of_representative": data.get("name_of_representative"),
        "representative_phone": data.get("representative_phone"),
        "representative_cell_phone": data.get("representative_cell_phone"),
        "representative_email": data.get("representative_email"),
        "street_of_warehouse": data.get("street_of_warehouse"),
        "store_or_warehouse_number": data.get("store_or_warehouse_number"),
        "province_of_warehouse": data.get("province_of_warehouse"),
        "warehouse_reference": data.get("warehouse_reference"),
        "local_administration": data.get("local_administration"),
        "warehouse_sector": data.get("warehouse_sector"),
        "operation_carried_out_in_premise": data.get("operation_carried_out_in_premise"),

    
        "media_file": data.get("media_file") if data.get("media_file") else None,
        "odoo_id": request.user.odoo_id
    }

      
        try:
            response = requests.post(odoo_url, headers=headers, json=odoo_data, timeout=10)
        
            if response.status_code == 200:
              
                return response.json()
            else:
                print(f"Error in Odoo. Status Code: {response.status_code}, Mensaje: {response.text}")
                raise Exception(f"Error sending data to Odoo: {response.text}")
    
        except requests.exceptions.RequestException as e:
            print(f"Odoo request failed: {str(e)}")
            raise Exception(f"Odoo connection error: {str(e)}")

     

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


        # Small correction for this enpoint, to adapt it correctly to the odoo flow.
        files = request.FILES.getlist('media_files')
        serializer = TaxPayerSerializer(data=request.data)

        #odoo part.
        if serializer.is_valid():
            try:
                with transaction.atomic():  
                    taxpayer = serializer.save()

                   
                    if len(files) > 5:
                        return Response({"error": "You can only upload a maximum of 5 files"}, status=status.HTTP_400_BAD_REQUEST)

                    
                    media_objects = [
                        TaxPayerMedia(taxpayer=taxpayer, media_file=file) for file in files
                    ]
                    TaxPayerMedia.objects.bulk_create(media_objects)

                   
                    odoo_response = self.send_to_odoo(request, request.data)

                    if odoo_response:
                       
                        return Response({"form_data": serializer.data, "odoo_response": odoo_response}, status=status.HTTP_201_CREATED)
                    else:
                       
                        raise Exception("Error sending data to Odoo.")  
            except Exception as e:
                
                return Response({"error": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"error": "Invalid data."}, status=status.HTTP_400_BAD_REQUEST)


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

            #Odoo part.
            if serializer.is_valid():
                try:
                    
                    with transaction.atomic():
                        
                        taxpayer_updated = serializer.save()

                        
                        odoo_response = self.send_update_to_odoo(request, request.data)

                        if odoo_response:
                            
                            return Response({
                                "form_data": serializer.data,
                                "odoo_response": odoo_response
                            }, status=status.HTTP_200_OK)
                        else:
                           
                            raise Exception("Error sending data to Odoo.")

                except Exception as e:
                    
                    return Response({"error": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    

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
