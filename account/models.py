from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class MyUser(AbstractUser):
	email=models.EmailField(unique=True)

class Profile(models.Model):
	user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
	profile_image=models.ImageField(upload_to='profile_image/%Y/',null=True,blank=True)
	birth_day=models.DateField(blank=True,null=True)

	def __str__(self):
		return f'profile:{self.user.username}'
