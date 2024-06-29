from django.contrib import admin
from .models import Message,Like,Comment,LikeComment,SavePost,GeneralProblem,Report,ReportProblem

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
	list_display=['id']

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


@admin.register(GeneralProblem)
class GeneralProblemAdmin(admin.ModelAdmin):
	list_display=['title']

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
	list_display=['user','content_object','general_report']

@admin.register(ReportProblem)
class ReportProblemAdmin(admin.ModelAdmin):
	list_display=['user',]