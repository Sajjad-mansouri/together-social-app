from django import template
from django.db.models import Q,Count

from social.models import Like,Message


register = template.Library()

@register.simple_tag(takes_context=True)
def liked(context,post):
	user=context['user']
	if post in user.like_set.values_list('post',flat=True):

		return True
	else:
		return False

@register.simple_tag(takes_context=True)
def get_like_id(context,post_id):
	user=context['user']
	try:
		like_id=Like.objects.get(user=user.id,post=post_id).id
	except Like.DoesNotExist:
		like_id=''

	return like_id

@register.simple_tag
def count_like(post_id):
	post=Message.objects.get(pk=post_id)
	fn=Like.objects.aggregate(like_count=Count('pk',filter=Q(post=post)))
	return fn['like_count']

@register.simple_tag(takes_context=True)
def is_saved(context,post_id):
	user=context['user']
	try:
		message=Message.objects.get(id=post_id)
		return user in message.saved_post.all() 

	except  Exception as e:
		print(e)

@register.simple_tag(takes_context=True)
def saved_post_id(context,post_id):
	user=context['user']
	try:
		message=Message.objects.get(id=post_id)
		return message.saved_posts.get(user=user).id
	except Exception as e:
		print(e)



@register.simple_tag(takes_context=True)
def user_profile_path(context):
	user=context['user']

	return f'/profile/{user.username}'