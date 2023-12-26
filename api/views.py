from rest_framework import generics
from rest_framework.parsers import FormParser,MultiPartParser

from .serializers import PostSerializer
from social.models import Message

class PostListApiView(generics.ListCreateAPIView):

	serializer_class=PostSerializer
	parser_classes=[FormParser,MultiPartParser]
	queryset=Message.objects.all()

