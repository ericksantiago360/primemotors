from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from .models import Item


@receiver(post_delete, sender=Item)
def delete_image_file_on_item_delete(sender, instance, **kwargs):
    """Borra del disco la imagen cuando se elimina el artículo."""
    if instance.image:
        instance.image.delete(save=False)


@receiver(pre_save, sender=Item)
def delete_old_image_file_on_replace(sender, instance, **kwargs):
    """Borra del disco la imagen anterior cuando se reemplaza por otra."""
    if not instance.pk:
        return

    old_image = Item.objects.filter(pk=instance.pk).values_list('image', flat=True).first()
    if old_image and old_image != instance.image.name:
        instance.image.storage.delete(old_image)
