from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from account.models import Contact,Notification
import datetime



@receiver(post_save,sender=Contact, dispatch_uid="my_unique_identifier")
def my_callback(sender,instance,created,raw ,**kwargs):
    if instance.access:
        verb=f'{instance.from_user} is following You'
    else:
        verb=f'{instance.from_user} is requesting follow You'

    last_notif=timezone.now()-datetime.timedelta(seconds=60)
    content_type=ContentType.objects.get_for_model(instance)
    object_id=instance.id
    similarity=Notification.objects.filter(user=instance.from_user,content_type=content_type,object_id=object_id,verb=verb,created__gt=last_notif)
    if not similarity:
        Notification.objects.create(user=instance.from_user,content_object=instance,verb=verb)
