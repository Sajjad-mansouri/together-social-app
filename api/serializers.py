from rest_framework import serializers
from social.models import Message

class PostSerializer(serializers.ModelSerializer):
	class Meta:
		model=Message
		fields='__all__'
