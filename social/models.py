from django.db import models
from django.conf import settings
from django.utils import timezone
from django.template.defaultfilters import truncatechars
from django.contrib.contenttypes.fields import GenericRelation,GenericForeignKey
from django.contrib.contenttypes.models import ContentType

def custom_upload(instance,filename):
	datetime=timezone.now()
	return f'uploads/{instance.user.username}/{datetime.year}/{datetime.month}'

class Message(models.Model):
	user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='messages')
	
	text=models.TextField()
	image=models.ImageField(upload_to=custom_upload)
	created=models.DateTimeField(auto_now_add=True)
	updated=models.DateTimeField(auto_now=True)
	like=models.ManyToManyField(settings.AUTH_USER_MODEL,through='Like')
	saved_post=models.ManyToManyField(settings.AUTH_USER_MODEL,through='SavePost',related_name='save_messages')
	comment=GenericRelation('Comment')
	reports=GenericRelation('Report',related_query_name='reports')
	def __str__(self):
		return f'{self.id}'

	class Meta:
		ordering=['-created']



class LikeSaveAbstract(models.Model):
	user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
	created=models.DateTimeField(auto_now_add=True)

	class Meta:
		abstract=True
class SavePost(LikeSaveAbstract):

	post=models.ForeignKey(Message,on_delete=models.CASCADE,related_name='saved_posts')
	class Meta:
		unique_together=['user','post']

class Like(LikeSaveAbstract):
	post=models.ForeignKey(Message,on_delete=models.CASCADE,related_name='likes')
	
	class Meta:
		unique_together=['user','post']
		


class Comment(models.Model):
	author=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='author_comments')
	parent=models.ForeignKey('self',on_delete=models.CASCADE,null=True,blank=True,related_name='comments')
	main_comment=models.ForeignKey('self',on_delete=models.CASCADE,null=True,blank=True,related_name='main_comments')
	comment=models.TextField()
	created=models.DateTimeField(auto_now_add=True)
	limit=models.Q(app_label='social',model='message')
	content_type=models.ForeignKey(ContentType,on_delete=models.CASCADE,limit_choices_to=limit)
	object_id=models.PositiveIntegerField()
	content_object=GenericForeignKey('content_type','object_id')
	like=models.ManyToManyField(settings.AUTH_USER_MODEL,through='LikeComment')

	class Meta:
		indexes=[
			models.Index(fields=['content_type','object_id'])
		]

class LikeComment(LikeSaveAbstract):
	comment=models.ForeignKey(Comment,on_delete=models.CASCADE)

	class Meta:
		unique_together=['user','comment']






class GeneralProblem(models.Model):
	title=models.CharField(max_length=200)
	created=models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.title


class Report(models.Model):
	user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)

	limit=models.Q(app_label='account',model='myuser') | models.Q(app_label='social',model='message')
	content_type=models.ForeignKey(ContentType,on_delete=models.CASCADE,limit_choices_to=limit)
	object_id=models.PositiveIntegerField()
	content_object=GenericForeignKey('content_type','object_id')

	general_report=models.ForeignKey(GeneralProblem,on_delete=models.CASCADE,null=True)
	account_pretending=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,null=True,blank=True,related_name='target_user')

	seen=models.BooleanField(default=False)
	seen_date_time=models.DateTimeField(null=True,blank=True)
	
	created=models .DateTimeField(auto_now_add=True)


class ReportProblem(models.Model):
	user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
	report=models.TextField()
	created=models.DateTimeField(auto_now_add=True)