from datetime import timedelta

from django.utils.timesince import timesince
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from rest_framework import serializers
from social.models import Message,Like,Comment,LikeComment,SavePost,GeneralProblem,Report
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

	def liked(self,obj):
		
		user=self._context['request'].user
		
		try:
			like_obj=user.like_set.get(post=obj)
		except:
			like_obj=None

		like_count=obj.likes.count()
		
		try:
			user_likes=user.like_set.values_list('post',flat=True)
		except AttributeError:
			user_likes=[]
		
		
		if obj.id in user_likes:
			
			return (True,like_obj.id, like_count)
		else:
			
			return (False,None,like_count)

	is_liked=serializers.SerializerMethodField('liked')

	def saved(self,obj):
		user=self._context['request'].user
		
		try:
			saved_obj=user.savepost_set.get(post=obj)
		except:
			saved_obj=None

		try:
			
			user_saves=user.savepost_set.values_list('post',flat=True)
		except AttributeError:
			user_saves=[]

		
		if obj.id in user_saves:
			return (True,saved_obj.id)
		else:
			return (False,None)

	is_saved=serializers.SerializerMethodField('saved')	

	def to_internal_value(self,data):
		
		user=self._context['request'].user.id
		data['user']=user
		return super().to_internal_value(data)

	def is_valid(self,raise_exception=False):

			valid=super().is_valid()
			
			return valid

	class Meta:
		model=Message
		fields=['id','text','image','created','owner','user','is_liked','is_saved']
		read_only_fields=['owner','is_liked']


class SearchSerializer(serializers.ModelSerializer):

	profile_image=serializers.ImageField(source='profile.profile_image')

	class Meta:
		model=get_user_model()
		fields=['first_name','last_name','username','profile_image']

class RelationSerializer(serializers.ModelSerializer):
	def get_relation(self,obj):
		username=self.context['owner']
		if self.context['relation']=='following':
			return obj.rel_to.get(from_user__username=username).id
		elif self.context['relation']=='follower':
			return obj.rel_from.get(to_user__username=username).id
	profile_image=serializers.ImageField(source='profile.profile_image')
	relation=serializers.SerializerMethodField('get_relation')
	class Meta:
		model=get_user_model()
		fields=['first_name','last_name','username','profile_image','relation']
class UserSerializer(serializers.ModelSerializer):
	profile_image=serializers.ImageField(source='profile.profile_image')
	class Meta:
		model=get_user_model()
		fields=['first_name','last_name','email','username','profile_image']

class ContactSerializer(serializers.ModelSerializer):

	def reverse(self,obj):
		return Contact.objects.filter(from_user=obj.to_user,to_user=obj.from_user).exists()
		

	reverse_following=serializers.SerializerMethodField('reverse')

	class Meta:
		model=Contact
		fields=['id','from_user','to_user','access','reverse_following']

	def to_internal_value(self,data):
		if not getattr(self.root,'partial',False):
			

			from_user=self._context['request'].user.id
			data['from_user']=from_user
		
		return super().to_internal_value(data)

	def create(self,validated_data):
		
		to_user=validated_data.get('to_user')
		access=False if to_user.profile.private else True
		validated_data['access']=access

		return Contact.objects.create(**validated_data)

class LikeSerializer(serializers.ModelSerializer):
	class Meta:
		model=Like
		fields=['id','user','post']

	def to_internal_value(self,data):
		user=self._context['request'].user.id
		data['user']=user
		
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
			print('try like commment')
			print(f'user: {user}')
			liked=obj.likecomment_set.get(user_id=user)
			print(f'liked: {liked}')
			data.update({"is_liked":True,"id":liked.id})
		except Exception as e:
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
		
		return super().to_internal_value(data)

	def create(self,validated_data):
		
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
		
		
		user=self._context['request'].user.id
		
		
		data['user']=user
		
		return super().to_internal_value(data)






class ChangePasswordSerializer(serializers.Serializer):
	old_password=serializers.CharField(required=True,write_only=True,max_length=200)
	password1=serializers.CharField(required=True,write_only=True,max_length=200)
	password2=serializers.CharField(required=True,write_only=True,max_length=200)

	def to_internal_value(self,data):
		
		return super().to_internal_value(data)

	def is_valid(self,raise_exception=False):
			
			valid=super().is_valid(raise_exception=True)
			
			return valid
	def validate_old_password(self,value):
		
		user=self._context['request'].user
		if not user.check_password(value):
			raise serializers.ValidationError('old password is not correct')
		return value

	def validate(self,data):
		
		
		if data['password1']!=data['password2']:
			raise serializers.ValidationError('doesnot match passwords')

		validate_password(data['password1'],self._context['request'].user)
		
		return data

	def save(self,**kwargs):
		password=self.validated_data['password1']
		user=self._context['request'].user
		user.set_password(password)
		user.save()
		return user


class GeneralReportSerializer(serializers.ModelSerializer):
	class Meta:
		model=GeneralProblem
		fields=['id','title']

class ReportSerializer(serializers.ModelSerializer):

	def to_internal_value(self,data):
		self.user=self._context['request'].user.id
		data['user']=self.user
		self.post_owner=data.pop('post_owner')
		if data['content_type']=='post':
			self.content_type='post'
		return super().to_internal_value(data)

	def follow(self,obj):
		try:
			print(self.user)
			print(self.post_owner)
			Contact.objects.get(from_user=self.user,to_user__username=self.post_owner)
			return True
		except Exception as e:
			print(e)
			return False

	is_following=serializers.SerializerMethodField('follow')
	def create(self,validated_data):
		

		user=validated_data.pop('user')
		object_id=validated_data['object_id']
		general_report=validated_data['general_report']
		if self.content_type=='post':
			content_object=Message.objects.get(id=object_id)
		elif self.content_type=='user':
			content_object=UserModel.objects.get(id=object_id)
		
		return Report.objects.create(	user=user,
										content_object=content_object,
										general_report=general_report
										)


		

	def is_valid(self,raise_exception=False):
		valid=super().is_valid(raise_exception=False)
		print(self.errors)
		
		return valid
	class Meta:
		model=Report
		fields=['id','user','object_id','general_report','is_following']
		# read_only_fields=['is_user_comment']