from datetime import timedelta

from django.utils.timesince import timesince
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from rest_framework import serializers
from social.models import Message,Like,Comment,LikeComment,SavePost
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from django.utils import timezone
from account.models import Contact,Profile


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


class SearchSerializer(serializers.ModelSerializer):
	profile_image=serializers.ImageField(source='profile.profile_image')
	class Meta:
		model=get_user_model()
		fields=['first_name','last_name','username','profile_image']

class UserSerializer(serializers.ModelSerializer):
	profile_image=serializers.ImageField(source='profile.profile_image')
	class Meta:
		model=get_user_model()
		fields=['first_name','last_name','email','username','profile_image']

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

class SavedPostSerializer(serializers.ModelSerializer):
	class Meta:
		model=SavePost
		fields=['id','user','post']

	def to_internal_value(self,data):
		user=self._context['request'].user.id
		data['user']=user
		
		return super().to_internal_value(data)

class ProfileSerializer(serializers.ModelSerializer):
	user=UserSerializer()
	class Meta:
		model=Profile
		fields=['id','user','profile_image','birth_day','bio','private']
	def is_valid(self,raise_exception=False):
		valid=super().is_valid(raise_exception=False)
		print('errors',self.errors)
		return valid
	def to_internal_value(self,data):
		print('to_internal_value',data)
		print(self._context['request'].content_type)
		return super().to_internal_value(data)


	def update(self,instance,validated_data):
		instance_user=instance.user
		user=validated_data.get('user')
		instance.private=validated_data.get('private',instance.private)
		instance.profile_image=validated_data.get('profile_image',instance.profile_image)
		instance.birth_day=validated_data.get('birth_day',instance.birth_day)
		instance.bio=validated_data.get('bio',instance.bio)
		if user:
			instance_user.first_name=user.get('first_name',instance_user.first_name)
			instance_user.last_name=user.get('last_name',instance_user.last_name)
			instance_user.email=user.get('email',instance_user.email)
			instance_user.username=user.get('username',instance_user.username)
			
			instance_user.save()
		print('user',user)
		instance.save()
		return instance


class profileSerializerReadOnly(serializers.ModelSerializer):
	class Meta:
		model=Profile
		fields=['profile_image']

class UserProfileSerializer(serializers.ModelSerializer):
	profile=profileSerializerReadOnly(read_only=True)
	class Meta:
		model=get_user_model()
		fields=['username','profile']





class CommentSerializer(serializers.ModelSerializer):
	def get_time(self,obj):
		return timesince(obj.created).split(',')[0]

	def user_comment(self,obj):
		user=self._context['request'].user.username
		if obj.author.username==user:
			return True
		else:
			return False
	def like(self,obj):
		user=self._context['request'].user.id
		like_count=obj.like.count()
		data={}
		try:
			
			liked=obj.likecomment_set.get(user_id=user)
			
			data.update({"is_liked":True,"id":liked.id})
		except Exception as e:
			print(e)
			data.update({'is_liked':False})
		data.update({'like_count':like_count})

		return data

	author=UserProfileSerializer()
	created=serializers.SerializerMethodField('get_time')
	is_user_comment=serializers.SerializerMethodField('user_comment')
	like_info=serializers.SerializerMethodField('like')
	def to_internal_value(self,data):
		user=self._context['request'].user.id
		data['author']={'username':user}
		print(data)
		return super().to_internal_value(data)

	def create(self,validated_data):
		print('validated_data',validated_data)
		author=validated_data.pop('author')
		object_id=validated_data['object_id']
		username=int(author['username'])
		comment=validated_data['comment']
		try:
			main_comment=validated_data['main_comment']
			parent=validated_data['parent']
		except:
			main_comment=None
			parent=None

		user=get_user_model().objects.get(id=username)
		message=Message.objects.get(id=object_id)
		return Comment.objects.create(content_object=message,
										author=user,
										comment=comment,
										parent=parent,
										main_comment=main_comment,)


		

	def is_valid(self,raise_exception=False):
		valid=super().is_valid(raise_exception=False)
		print(self.errors)
		return valid
	class Meta:
		model=Comment
		fields=['id','comment','object_id','author','parent','main_comment','created','is_user_comment','like_info']
		# read_only_fields=['is_user_comment']


class LikeCommentSerializer(serializers.ModelSerializer):
	class Meta:
		model=LikeComment
		fields=['id','user','comment']

	def to_internal_value(self,data):
		print('++++++++++++=')
		print(type(data))
		user=self._context['request'].user.id
		print('*********')
		data['user']=user
		print(data)
		return super().to_internal_value(data)






class ChangePasswordSerializer(serializers.Serializer):
	old_password=serializers.CharField(required=True,write_only=True,max_length=200)
	password1=serializers.CharField(required=True,write_only=True,max_length=200)
	password2=serializers.CharField(required=True,write_only=True,max_length=200)

	def to_internal_value(self,data):
		
		return super().to_internal_value(data)

	def is_valid(self,raise_exception=False):
			print('is_valid')
			valid=super().is_valid(raise_exception=True)
			print('value in is_valid')
			return valid
	def validate_old_password(self,value):
		print('validate_old_password')
		user=self._context['request'].user
		if not user.check_password(value):
			raise serializers.ValidationError('old password is not correct')
		return value

	def validate(self,data):
		print('validate')
		
		if data['password1']!=data['password2']:
			raise serializers.ValidationError('doesnot match passwords')

		validate_password(data['password1'],self._context['request'].user)
		print('end validate')
		return data

	def save(self,**kwargs):
		password=self.validated_data['password1']
		user=self._context['request'].user
		user.set_password(password)
		user.save()
		return user