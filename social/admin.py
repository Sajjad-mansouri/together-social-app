from django.contrib import admin
from .models import Message,Like

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
	list_display=['user','title']

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
	list_display=['user','post']