from django.conf import settings
from rest_framework import serializers
from .models import Career, Requirement, Question, Option, Answer, CareerApplication



class RequirementSerializer(serializers.Serializer):
    description = serializers.CharField()

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = '__all__'

class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = '__all__'
        

class OptionInputSerializer(serializers.Serializer):
    text = serializers.CharField()
    is_correct = serializers.BooleanField(default=False)


class QuestionInputSerializer(serializers.Serializer):
    text = serializers.CharField()
    question_type = serializers.ChoiceField(choices=Question.QUESTION_TYPES)
    options = OptionInputSerializer(many=True, required=False)



class CareerInputSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    requirements = RequirementSerializer(many=True)


class CareerSerializer(serializers.ModelSerializer):
    requirements = serializers.SerializerMethodField()
    
    def get_requirements(self, obj):
        requirements = Requirement.objects.filter(career=obj)
        return RequirementSerializer(requirements, many=True).data
    class Meta:
        model = Career
        fields = "__all__"

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = '__all__'
        
class AnswerInputSerializer(serializers.Serializer):
    question_id = serializers.CharField()
    selected_options = serializers.ListField(child=serializers.CharField(), required=False)
    
    text_answer = serializers.CharField(required=False)
    full_name = serializers.CharField()
    email = serializers.EmailField()
        

class CareerApplicationInputSerializer(serializers.Serializer):
    career_id = serializers.CharField()
    user_id = serializers.FileField()
    resume = serializers.FileField()
    full_name = serializers.CharField()
    email = serializers.EmailField()
    primary_profession = serializers.CharField()
    project_link = serializers.CharField()
    github_repo = serializers.CharField()
    country = serializers.CharField(required=False)
    state = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    

class CareerApplicationSerializer(serializers.ModelSerializer):
    
    def to_representation(self, instance):
        # Start with the default representation
        representation = super().to_representation(instance)

        # Add custom fields
        if instance.resume:
            representation['resume'] = f"{settings.BASE_URL}{instance.resume.url}"
        else:
            representation['resume'] = None

        if instance.user_id:
            representation['user_id'] = f"{settings.BASE_URL}{instance.user_id.url}"
        else:
            representation['user_id'] = None

        return representation
    
    class Meta:
        model = CareerApplication
        fields = "__all__"
