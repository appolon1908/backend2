from django.http import Http404
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.text import slugify
from django.utils.timezone import now

from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticated


from .serializers import (
            BlogInputSerializer, 
            BlogOutputSerializer, 
            CommentSerializer,
            ModerateBlogCommentSerializer, 
            AddCommentSerialier)

from blog_app.models import Blog, Tag, Category
from auth_app.models import Visitor
from cms.models import HeaderTitle
from cms.serializers import HeaderTitleSerializer

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class BlogViewSet(ViewSet):
    pagination_class = LimitOffsetPagination
    
    def get_permissions(self):
        if self.action in {"list", "retrieve", "get_blog_header_title"}:
            return [AllowAny()]
        if self.action in {"like", "add_comment"}:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_object(self, *args, **kwargs):
        """
        Retrieve a published Blog object by its primary key (pk).

        Args:
            pk (int): The primary key of the Blog object to retrieve.

        Returns:
            Blog: The Blog object with the specified primary key and published status.
            Response: A 404 Not Found response if the Blog object does not exist.
        """
        try:
            return Blog.objects.get(status=Blog.PUBLISHED, id=kwargs.get('pk'), **kwargs)
        except Blog.DoesNotExist:
            raise Http404
    
    
    @swagger_auto_schema(
        operation_description="List Blogs",
        operation_summary="List Blogs",
        tags=["Blog"],
    )
    def list(self, request):
        """
        Handles the listing of published blog posts with pagination.
        Args:
            request (Request): The HTTP request object.
        Returns:
            Response: A paginated response containing serialized blog posts if pagination is applied,
                      otherwise a response containing all serialized blog posts.
        """
        
        paginator = self.pagination_class()
        
        blogs = Blog.objects.filter(status=Blog.PUBLISHED)
        
        category = request.query_params.get('category')
        tags = request.query_params.getlist('tags')
        title = request.query_params.get('title')
        author = request.query_params.get('author')
        order_by = request.query_params.get('order_by')

        if category:
            blogs = blogs.filter(category__name=category)
        
        if tags:
            blogs = blogs.filter(tags__name__in=tags).distinct()
        
        if title:
            blogs = blogs.filter(title__icontains=title)
        
        if author:
            blogs = blogs.filter(author__first_name__iexact=author) | blogs.filter(author__last_name__iexact=author)
        
        if order_by:
            if order_by in ['views', '-views', 'likes', '-likes', 'published_at', '-published_at']:
                blogs = blogs.order_by(order_by)

        result_page = paginator.paginate_queryset(blogs, request)
        
        if result_page is not None:
            serializer = BlogOutputSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        return Response(BlogOutputSerializer(blogs, many=True).data)
    
    @swagger_auto_schema(
        operation_description="Retrieve Blogs",
        operation_summary="Retrieve Blogs",
        tags=["Blog"],
    )
    def retrieve(self, request, pk=None):
        
        blog = Blog.objects.filter(status=Blog.PUBLISHED, id=pk).first()
        
        if blog:
        
            blog.views = blog.views + 1
            blog.save()
            serializer = BlogOutputSerializer(blog)
            return Response(serializer.data)
        return Response({"error": "No blog found"}, status=status.HTTP_404_NOT_FOUND)
    
    
    @swagger_auto_schema(
        operation_description="Create Blogs",
        operation_summary="Create Blogs",
        tags=["Blog"],
        request_body=BlogInputSerializer
    )
    def create(self, request):
        serializer = BlogInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        tag_input = serializer.validated_data.get('tags', [])
        category = serializer.validated_data.get('category')
        status_ = serializer.validated_data.get('status')
        scheduled_date = serializer.validated_data.get('scheduled_date')
        
        title_slug = slugify(serializer.validated_data['title'])
        
        if status_ == Blog.SCHEDULED and not scheduled_date:
            return Response({'error': 'Scheduled date is required for scheduled blogs'}, status=status.HTTP_400_BAD_REQUEST)
        
        if Blog.objects.filter(slug=title_slug).exists():
            return Response({'error': 'Blog with this title already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        tags = []
        for tag_name in tag_input:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            tags.append(tag)
            
        category_instance = None
        if category:
            category_instance, created = Category.objects.get_or_create(name=category)
        
        blog = Blog.objects.create(
            title=serializer.validated_data['title'],
            content=serializer.validated_data['content'],
            status=serializer.validated_data['status'],
            category=category_instance,
            author=request.user,
            scheduled_date = scheduled_date,
            published_at = now() if status_ == Blog.PUBLISHED else None,
        )
        
        # handle tags saving
        blog.tags.set(tags)
        
        image_file = request.FILES.get('image')
        if image_file:
            blog.image.save(image_file.name, image_file)
        
        video_file = request.FILES.get('video')
        if video_file:
            blog.video.save(video_file.name, video_file)
        
        blog.save()
        
        output_serializer = BlogOutputSerializer(blog)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        
    
    @swagger_auto_schema(
        operation_description="Update Blogs",
        operation_summary="Update Blogs",
        tags=["Blog"],
        request_body=BlogInputSerializer
    )
    def update(self, request, pk=None):
        blog = self.get_object(pk=pk, author=request.user)
        serializer = BlogInputSerializer(blog, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        tag_input = serializer.validated_data.get('tags')
        category = serializer.validated_data.get('category', None)
        blog_status = serializer.validated_data.get('status', None)
        
        if blog_status == Blog.SCHEDULED:
            scheduled_date = serializer.validated_data.get("scheduled_date", None)
            if not scheduled_date:
                return Response({'error': 'Scheduled date is required for scheduled blogs'}, status=status.HTTP_400_BAD_REQUEST)
            
            blog.scheduled_date = scheduled_date
            
        elif blog_status == Blog.PUBLISHED:
            blog.published_at = now()
        
        tags = []
        if tag_input:
            for tag_name in tag_input:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                tags.append(tag)
            
        if category:
            category_instance, created = Category.objects.get_or_create(name=category)
            blog.category = category_instance
        # else:
        #     blog.category = blog.category
        
        blog.title = serializer.validated_data.get('title', None) or blog.title
        blog.content = serializer.validated_data.get("content", None) or blog.content
        blog.status = blog_status or blog.status
        
        # handle tags saving
        if tags:
            blog.tags.set(tags)
        
        image_file = request.FILES.get('image')
        if image_file:
            blog.image.save(image_file.name, image_file)
        
        video_file = request.FILES.get('video')
        if video_file:
            blog.video.save(video_file.name, video_file)
        
        blog.save()
        
        output_serializer = BlogOutputSerializer(blog)
        return Response(output_serializer.data)
    
    
    @swagger_auto_schema(
        operation_description="Like a Blog",
        operation_summary="Like a Blog",
        tags=["Blog"]
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        blog = self.get_object(pk=pk)
        if not blog:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        blog.likes.add(request.user)
        blog.save()
        
        return Response({'status': 'blog liked'})
    
    @swagger_auto_schema(
        operation_description="Add a comment on blog",
        operation_summary="Add a comment on blog",
        tags=["Blog"],
        request_body=AddCommentSerialier
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_comment(self, request, pk=None):
        blog = self.get_object(pk=pk)
        if not blog:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        serializer = AddCommentSerialier(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        comment_text = serializer.validated_data.get('comment')

        comment = blog.comments.create(user=request.user, content=comment_text)
        comment.save()
        
        return Response({'status': 'comment added'}, status=status.HTTP_201_CREATED)
    
    
    @swagger_auto_schema(
        operation_description="Moderate on blog comment",
        operation_summary="Moderate on blog comment",
        tags=["Blog"],
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def moderate_comment(self, request, pk=None):
        blog = self.get_object(pk=pk, author=request.user)
        if not blog:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        comment_id = request.data.get('comment_id')
        can_publish_comment = request.data.get('can_publish_comment')
        if comment_id is None or can_publish_comment is None:
            return Response({'error': 'Comment ID and can_publish_comment is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            comment = blog.comments.get(id=comment_id)
        except blog.comments.model.DoesNotExist:
            return Response({'error': 'Comment not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ModerateBlogCommentSerializer(comment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({'status': 'comment moderated'}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="List all comments of a blog",
        operation_summary="List all comments of a blog",
        tags=["Blog"],
    )
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def list_blog_comments(self, request, pk=None):
        blog = self.get_object(pk=pk, author=request.user)
        if not blog:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        comments = blog.comments.all()
        serializer = CommentSerializer(comments, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Get Hero header title for blog page",
        operation_summary="Get Hero header title for blog page",
        tags=["Blog"],
    )
    @action(detail=False, methods=['get'], url_path="hero/header-title/get")
    def get_blog_header_title(self, request):
        header_title = HeaderTitle.objects.filter(page='blog').order_by('-created_at').first()
        
        if not header_title:
            return Response({'message': 'No header title found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(HeaderTitleSerializer(header_title).data, status=status.HTTP_200_OK)
    

    @swagger_auto_schema(
        operation_description="Create Hero Header Title for blog page",
        operation_summary="Create Hero Header Title for blog page",
        tags=["Blog"],
        request_body=HeaderTitleSerializer
    )
    @action(detail=False, methods=['post'], url_path="hero/header-title")
    def create_blog_header_title(self, request):
        serializer = HeaderTitleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(page='blog')
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

def robots_txt(request):
    content = f"User-agent: *\nDisallow:\nSitemap: {settings.BASE_URL}/sitemap.xml"
    return HttpResponse(content, content_type="text/plain")