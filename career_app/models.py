import uuid
from django.db import models
from auth_app.models import User




def generate_id():
    return uuid.uuid4().hex



class Career(models.Model):
    id = models.CharField(primary_key=True, default=generate_id, editable=False, max_length=256)
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Requirement(models.Model):
    id = models.CharField(primary_key=True, default=generate_id, editable=False, max_length=256)
    career = models.ForeignKey(Career, related_name="requirements", on_delete=models.CASCADE)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.description

class Question(models.Model):
    SINGLE_CHOICE = 'SINGLE_CHOICE'
    MULTIPLE_CHOICE = 'MULTIPLE_CHOICE'
    TEXT = 'TEXT'

    QUESTION_TYPES = [
        (SINGLE_CHOICE, 'Single Choice'),
        (MULTIPLE_CHOICE, 'Multiple Choice'),
        (TEXT, 'Text'),
    ]
    id = models.CharField(primary_key=True, default=generate_id, editable=False, max_length=256)
    career = models.ForeignKey(Career, related_name="questions", on_delete=models.CASCADE)
    text = models.CharField(max_length=500)
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPES)

    def __str__(self):
        return self.text

class Option(models.Model):
    id = models.CharField(primary_key=True, default=generate_id, editable=False, max_length=256)
    question = models.ForeignKey(Question, related_name="options", on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class Answer(models.Model):
    id = models.CharField(primary_key=True, default=generate_id, editable=False, max_length=256)
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField(max_length=256)
    full_name = models.CharField(max_length=256)
    question = models.ForeignKey(Question, related_name="answers", on_delete=models.CASCADE)
    selected_options = models.ManyToManyField(Option, blank=True)  # For multiple-choice
    text_answer = models.TextField(blank=True, null=True)  # For text answers
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.question.text}"
    

class CareerApplication(models.Model):
    id = models.CharField(
        primary_key=True, 
        editable=False, default=generate_id, max_length=70
    )
    career = models.ForeignKey(Career, on_delete=models.DO_NOTHING, null=True, blank=True)
    user_id = models.FileField(upload_to="career/", null=True, blank=True)
    resume = models.FileField(upload_to="career/", null=True, blank=True)
    
    full_name = models.CharField(max_length=256)
    email = models.EmailField(max_length=256)
    primary_profession = models.CharField(max_length=256, null=True, blank=True)
    project_link = models.CharField(max_length=256, null=True, blank=True)
    github_repo = models.CharField(max_length=256, null=True, blank=True)
    
    city = models.CharField(max_length=256, null=True, blank=True)
    state = models.CharField(max_length=256, null=True, blank=True)
    country = models.CharField(max_length=256, null=True, blank=True)
    
    