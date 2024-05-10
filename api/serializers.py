from datetime import timedelta
from django.utils.timesince import timesince


from rest_framework import serializers
from social.models import Message
from django.contrib.auth import get_user_model
from django.utils import timezone
from account.models import Contact,Profile
from social.models import Like

UserModel=get_user_model()


class PostSerializer(serializers.ModelSerializer):
	def get_author(self,obj):
		
		try:
			image_url=obj.user.profile.profile_image.url
		except ValueError:

			image_url=''
		return {
			'username':obj.user.username,
			'profile_image':image_url
		}

	owner=serializers.SerializerMethodField('get_author')

	def to_internal_value(self,data):
		print(data)
		user=self._context['request'].user.id
		data['user']=user
		return super().to_internal_value(data)

	def is_valid(self,raise_exception=False):

			valid=super().is_valid()
			print(self.errors)
			return valid

	class Meta:
		model=Message
		fields=['id','text','image','created','owner','user']
		read_only_fields=['owner']



class UserSerializer(serializers.ModelSerializer):
	class Meta:
		model=get_user_model()
		fields=['first_name','last_name','email','username']

class ContactSerializer(serializers.ModelSerializer):
	class Meta:
		model=Contact
		fields=['id','from_user','to_user']

	def to_internal_value(self,data):
		from_user=self._context['request'].user.id
		data['from_user']=from_user
		return super().to_internal_value(data)

class LikeSerializer(serializers.ModelSerializer):
	class Meta:
		model=Like
		fields=['id','user','post']

	def to_internal_value(self,data):
		user=self._context['request'].user.id
		data['user']=user
		print(data)
		return super().to_internal_value(data)


class ProfileSerializer(serializers.ModelSerializer):
	user=UserSerializer()
	class Meta:
		model=Profile
		fields=['id','user','profile_image','birth_day']



	def update(self,instance,validated_data):
		instance_user=instance.user
		user=validated_data.get('user')
		instance.profile_image=validated_data.get('profile_image',instance.profile_image)
		
		if user:
			instance_user.first_name=user.get('first_name',instance_user.first_name)
			instance_user.last_name=user.get('last_name',instance_user.last_name)
			instance_user.email=user.get('email',instance_user.email)
			instance_user.username=user.get('username',instance_user.username)
			instance_user.save()
		instance.save()
		return instance



