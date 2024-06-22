from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey



class MyUser(AbstractUser):
	email=models.EmailField(unique=True)


class Profile(models.Model):
	user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
	profile_image=models.ImageField(upload_to='profile_image/%Y/',null=True,blank=True,default='profile_image/default/blank-profile.png')
	contact=models.ManyToManyField('self',through='Contact',symmetrical=False)
	bio=models.TextField(blank=True)
	link=models.URLField(blank=True)
	private=models.BooleanField(default=False)
	
	birth_day=models.DateField(blank=True,null=True)

	def __str__(self):
		return f'profile:{self.user.username}'


class Contact(models.Model):
	from_user=models.ForeignKey(MyUser,on_delete=models.CASCADE,related_name='rel_from')
	to_user=models.ForeignKey(MyUser,on_delete=models.CASCADE,related_name='rel_to')
	access=models.BooleanField(default=True)
	created=models.DateTimeField(auto_now_add=True)
	class Meta:
		unique_together=['from_user','to_user']




class Notification(models.Model):
	user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
	content_type=models.ForeignKey(ContentType,on_delete=models.CASCADE)
	object_id=models.PositiveIntegerField()
	content_object=GenericForeignKey('content_type','object_id')
	verb=models.CharField(max_length=300)
	created=models.DateTimeField(auto_now_add=True)
	seen=models.BooleanField(default=False)

	class Meta:
		indexes=[models.Index(fields=['content_type','object_id'])]