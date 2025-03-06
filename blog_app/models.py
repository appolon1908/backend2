import uuid
from django.db import models
from django.utils.text import slugify
from django.utils.timezone import now
from django.contrib.auth import get_user_model



User = get_user_model()


def generate_id():
    return uuid.uuid4().hex

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Blog(models.Model):
    DRAFT = 'DRAFT'
    PUBLISHED = 'PUBLISHED'
    SCHEDULED = 'SCHEDULED'

    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (PUBLISHED, 'Published'),
        (SCHEDULED, 'Scheduled'),
    ]
    id = models.CharField(
        primary_key=True, 
        editable=False, default=generate_id, max_length=70
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    content = models.TextField()
    image = models.ImageField(upload_to='blogs/images/', blank=True, null=True)
    video = models.FileField(upload_to='blogs/videos/', blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blogs')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='blogs')
    tags = models.ManyToManyField(Tag, blank=True, related_name='blogs')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT)
    scheduled_date = models.DateTimeField(blank=True, null=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.PositiveIntegerField(default=0)
    likes = models.ManyToManyField(User, through='Like', related_name='liked_blogs')

    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.TextField(max_length=160, blank=True)
    
    @property
    def total_likes(self):
        return self.likes.count()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Like(models.Model):
    id = models.CharField(
        primary_key=True, 
        editable=False, default=generate_id, max_length=70
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class Comment(models.Model):
    id = models.CharField(
        primary_key=True, 
        editable=False, default=generate_id, max_length=70
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    can_publish_comment = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user} on {self.blog}"


class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='bookmarked_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    
class BlogViewer(models.Model):
    id = models.CharField(
        primary_key=True, 
        editable=False, default=generate_id, max_length=70
    )
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='blog_views')
    viewer = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True, related_name='blog_viewer')
    ip_address = models.GenericIPAddressField()
    view_duration = models.DurationField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('blog', 'ip_address')
        
    def __str__(self):
        return f"View by {self.ip_address} on {self.blog}"