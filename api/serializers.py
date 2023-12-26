from rest_framework import serializers
from social.models import Message
from django.contrib.auth import get_user_model

class PostSerializer(serializers.ModelSerializer):
	class Meta:
		model=Message
		fields='__all__'

class UserSerializer(serializers.ModelSerializer):
	class Meta:
		model=get_user_model()
		fields=['username']