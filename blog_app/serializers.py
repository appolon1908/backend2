from django.conf import settings
from rest_framework import serializers
from .models import Blog, Tag, Category, Comment, Like

from auth_app.serializers import UserSerializer, GetShortUserDetailsSerializer

class BlogInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    content = serializers.CharField()
    image = serializers.ImageField(required=False)
    video = serializers.FileField(required=False)
    category = serializers.CharField(required=False)
    tags = serializers.ListField(required=False, child=serializers.CharField())
    status = serializers.ChoiceField(choices=Blog.STATUS_CHOICES)
    scheduled_date = serializers.DateTimeField(required=False)
    
    
    
class CommentSerializer(serializers.ModelSerializer):
    user = GetShortUserDetailsSerializer(read_only=True)
    class Meta:
        model = Comment
        fields = ['id', 'content', 'user', 'can_publish_comment', 'blog', 'created_at']
        read_only_fields = ['id', 'created_at']
        

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']
        read_only_fields = ['id']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']
    

class BlogOutputSerializer(serializers.ModelSerializer):
    comment = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    author = GetShortUserDetailsSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    
    def get_comment(self, obj):
        comment = Comment.objects.filter(blog=obj, can_publish_comment=True)
        return CommentSerializer(comment, many=True).data
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        image = instance.image.url if instance.image else None
        data['image'] = f"{settings.BASE_URL}{image}" if image else None
        video = instance.video.url if instance.video else None
        data['video'] = f"{settings.BASE_URL}{video}" if video else None
        return data
    
    class Meta:
        model = Blog
        fields = [
            'id', 'title', 'content',
            'image', 'video', 'author', 
            'category', 'tags', 'status', 
            'views', 'likes', 'total_likes', 
            'published_at', 'scheduled_date', 
            'created_at', 'updated_at', 'comment']
        read_only_fields = ['id', 'created_at', 'updated_at']
        

class ModerateBlogCommentSerializer(serializers.Serializer):
    can_publish_comment = serializers.BooleanField()
    comment_id = serializers.CharField()
    
    def update(self, instance, validated_data):
        instance.can_publish_comment = validated_data.get('can_publish_comment', instance.can_publish_comment)
        instance.save()
        return instance
    

class AddCommentSerialier(serializers.Serializer):
    comment = serializers.CharField()
    