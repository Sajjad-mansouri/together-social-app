from django.db import models
from django.conf import settings
from django.utils import timezone
from django.template.defaultfilters import truncatechars


def custom_upload(instance,filename):
	datetime=timezone.now()
	return f'uploads/{instance.user.username}/{datetime.year}/{datetime.month}'

class Message(models.Model):
	user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='messages')
	title=models.CharField(max_length=200)
	text=models.TextField()
	image=models.ImageField(upload_to=custom_upload)
	created=models.DateTimeField(auto_now_add=True)
	updated=models.DateTimeField(auto_now=True)
	like=models.ManyToManyField(settings.AUTH_USER_MODEL,through='Like')
	def __str__(self):
		return f'{self.user}-{truncatechars(self.title,10)}'

	class Meta:
		ordering=['-created']



class Like(models.Model):
	user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='likes')
	post=models.ForeignKey(Message,on_delete=models.CASCADE,related_name='likes')
	created=models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together=['user','post']

