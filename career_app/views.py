from django.conf import settings

from .serializers import *
from .models import Career, CareerApplication, Requirement, Answer

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet, ModelViewSet
from drf_yasg.utils import swagger_auto_schema

from notification.service import EmailService

class CareerViewSet(ViewSet):
    queryset = Career.objects.all()
    serializer_class = CareerSerializer
    
    @swagger_auto_schema(
        operation_description="Candidate job application form",
        operation_summary="Candidate job application form",
        tags=["Career"],
        request_body=CareerInputSerializer
    )
    def create(self, request):
        serializer = CareerInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        requirements = serializer.validated_data.pop("requirements")
        
        career = Career.objects.create(**serializer.validated_data)

        Requirement.objects.bulk_create([
            Requirement(career=career, description=req.get('description'))
            for req in requirements
        ])
        return Response({"message": "Career created successfully"}, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        operation_description="List all career openings",
        operation_summary="List all career openings",
        tags=["Career"]
    )
    def list(self, request):
        career = Career.objects.all()
        return Response(CareerSerializer(career, many=True).data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Retrieve a career opening",
        operation_summary="Retrieve a career opening",
        tags=["Career"],
    )
    def retrieve(self, request, pk=None):
        career = Career.objects.filter(id=pk).first()
        return Response(
            CareerSerializer(career).data,
            status=status.HTTP_200_OK
        )
        
        
    @swagger_auto_schema(
        operation_description="List all applications for a career opening",
        operation_summary="List all applications for a career opening",
        tags=["Career"],
    )
    @action(methods=["GET"], detail=True)
    def applications(self, request, pk=None):
        career = Career.objects.filter(id=pk)
        
        if not career.exists():
            return Response({'error': 'Career not found'}, status=status.HTTP_404_NOT_FOUND)
        
        applications = CareerApplication.objects.filter(
            career=career.first()
        )
        return Response(CareerApplicationSerializer(applications, many=True).data, status=status.HTTP_200_OK)
    
    
    @swagger_auto_schema(
        operation_description="Candidate application form for a career opening",
        operation_summary="Candidate application form for a career opening",
        tags=["Career"],
        request_body=CareerApplicationInputSerializer
    )
    @action(methods=['POST'], detail=False, url_path="application")
    def create_application(self, request):
        serializer = CareerApplicationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        career = Career.objects.filter(id=serializer.validated_data.get("career_id"))
        
        if not career.exists():
            return Response({'error': 'Career not found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            existing_application = CareerApplication.objects.filter(
                career=career.first(),
                email=serializer.validated_data.get("email")
            )
            
            if existing_application.exists():
                return Response({'error': 'You have already applied for this job'}, status=status.HTTP_400_BAD_REQUEST)
            
            career_application = CareerApplication.objects.create(
                career=career.first(),
                **serializer.validated_data
            )
            
            user_id_url = settings.BASE_URL + career_application.user_id.url if career_application.user_id else None
            resume_url = settings.BASE_URL + career_application.resume.url if career_application.resume else None
            # send email to admin
            EmailService.send_async(
                template="career_application.html",
                subject="New Career Application",
                recipients=[settings.ADMIN_EMAIL], # admin email
                context={
                    "career": career_application.career.title,
                    "full_name": career_application.full_name,
                    "user_id": user_id_url,
                    "email": career_application.email,
                    "primary_profession": career_application.primary_profession,
                    "project_link": career_application.project_link,
                    "github_repo": career_application.github_repo,
                    "resume": resume_url,
                    "country": career_application.country,
                    "state": career_application.state,
                    "city": career_application.city,
                }
            )
            
            # send email to the user
            EmailService.send_async(
                template="career_application_confirmation.html",
                subject="Career Application Confirmation",
                recipients=[career_application.email],
                context={
                    "career": career_application.career.title,
                    "full_name": career_application.full_name,
                }
            )
            return Response(CareerApplicationSerializer(career_application).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        
        
    
    @swagger_auto_schema(
        operation_description="List Candidate job applications",
        operation_summary="List Candidate job applications",
        tags=["Career"]
    )
    @action(methods=['GET'], detail=False, url_path="applications")
    def list_applications(self, request):
        
        career_application = CareerApplication.objects.all()
        
        return Response(CareerApplicationSerializer(career_application, many=True).data, status=status.HTTP_201_CREATED)
        
    @swagger_auto_schema(
        operation_description="Retrieve Candidate job applications",
        operation_summary="Retrieve Candidate job applications",
        tags=["Career"]
    )
    @action(methods=['GET'], detail=False, url_path="applications/(?P<pk>[a-z,A-Z,0-9]+)")
    def retrieve_application(self, request, pk=None):
        
        career_application = CareerApplication.objects.filter(id=pk).first()
        
        return Response(CareerApplicationSerializer(career_application).data, status=status.HTTP_201_CREATED)
        
    
    @swagger_auto_schema(
        operation_description="Career application questions form",
        operation_summary="Career application questions form",
        tags=["Career"],
        request_body=QuestionInputSerializer
    )
    @action(methods=['POST'], detail=False, url_path="(?P<pk>[a-z,A-Z,0-9]+)/question")
    def create_application_question(self, request, pk=None):
        
        serializer = QuestionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        career = Career.objects.filter(id=pk)
        
        if not career.exists():
            return Response({'error': 'Career not found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            question_type = serializer.validated_data.get("question_type")
            
            if question_type in [Question.SINGLE_CHOICE, Question.MULTIPLE_CHOICE] and not serializer.validated_data.get("options"):
                return Response({'error': 'Options are required for single and multiple choice questions'}, status=status.HTTP_400_BAD_REQUEST)
            
            options = serializer.validated_data.pop("options", None)
            question = Question.objects.create(
                career=career.first(),
                **serializer.validated_data
            )
            if options:
                Option.objects.bulk_create([
                    Option(question=question, text=option.get('text'), is_correct=option.get('is_correct'))
                    for option in options
                ])
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(QuestionSerializer(question).data, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        operation_description="Career question answer form",
        operation_summary="Career question answer form",
        tags=["Career"],
        request_body=AnswerInputSerializer
    )
    @action(methods=['POST'], detail=False, url_path="(?P<question_id>[a-z,A-Z,0-9]+)/answer")
    def answer_career_question(self, request, question_id=None):
        question = Question.objects.filter(id=question_id)
        
        if not question.exists():
            return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = AnswerInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            selected_options_input = serializer.validated_data.pop("selected_options", None)
            text_answer = serializer.validated_data.pop("text_answer", None)
            
            if not selected_options_input and not text_answer:
                return Response({'error': 'Answer is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            selected_options = []
            
            if selected_options_input:
                selected_options = Option.objects.filter(id__in=selected_options)
            
            answer = Answer.objects.create(
                question=question.first(),
                selected_options=selected_options,
                text_answer=text_answer,
                full_name=serializer.validated_data.get("full_name"),
                email=serializer.validated_data.get("email")
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(AnswerSerializer(answer).data, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        operation_description="List answers for a career question",
        operation_summary="List answers for a career question",
        tags=["Career"]
    )
    @action(methods=['GET'], detail=False, url_path="(?P<question_id>[a-z,A-Z,0-9]+)/answers")
    def get_career_question_answer(self, requst, question_id=None):
        question = Question.objects.filter(id=question_id)
        
        if not question.exists():
            return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)
        
        answers = Answer.objects.filter(question=question.first())
        
        return Response(AnswerSerializer(answers, many=True).data, status=status.HTTP_200_OK)