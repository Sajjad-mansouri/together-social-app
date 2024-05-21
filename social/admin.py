from django.contrib import admin
from .models import Message,Like,Comment,LikeComment,SavePost

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
	list_display=['user']

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
	list_display=['user','post']

@admin.register(SavePost)
class SavePostAdmin(admin.ModelAdmin):
	list_display=['user','post']
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
	list_display=['comment','content_type','object_id']

@admin.register(LikeComment)
class LikeCommentAdmin(admin.ModelAdmin):
	list_display=['user','comment']
