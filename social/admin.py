from django.contrib import admin
from .models import Message,Like,Comment

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
	list_display=['user','title']

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
	list_display=['user','post']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
	list_display=['comment','content_type','object_id']