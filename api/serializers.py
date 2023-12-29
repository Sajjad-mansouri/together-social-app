from rest_framework import serializers
from social.models import Message
from django.contrib.auth import get_user_model

from account.models import Contact

UserModel=get_user_model()

class PostSerializer(serializers.ModelSerializer):
	class Meta:
		model=Message
		fields='__all__'

class UserSerializer(serializers.ModelSerializer):
	class Meta:
		model=get_user_model()
		fields=['username']

class ContactSerializer(serializers.ModelSerializer):
	class Meta:
		model=Contact
		fields=['id','from_user','to_user']

	def to_internal_value(self,data):
		from_user=self._context['request'].user.id
		data['from_user']=from_user
		return super().to_internal_value(data)