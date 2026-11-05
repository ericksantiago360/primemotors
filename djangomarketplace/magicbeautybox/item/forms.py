from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from .models import Item

INPUT_CLASSES =  'w-full py-4 px-6 rounded-xl border'
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB; nginx también limita el cuerpo a 6 MB


def validate_image_size(image):
    if isinstance(image, UploadedFile) and image.size > MAX_IMAGE_BYTES:
        raise ValidationError('La imagen no puede pesar más de 5 MB.')
    return image


class NewItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields =('category', 'name', 'description', 'price', 'image', )
        labels = {
            'category': 'categoría',
            'name': 'nombre',
            'description': 'descripción',
            'price': 'precio',
            'image': 'imagen',
        }
        widgets = {
            'category' : forms.Select(attrs={
                'class': INPUT_CLASSES
            }),
            'name' : forms.TextInput(attrs={
                'class': INPUT_CLASSES
            }),
            'description': forms.Textarea(attrs={
                'class': INPUT_CLASSES
            }),
            'price': forms.TextInput(attrs={
                'class': INPUT_CLASSES
            }),
            'image':forms.FileInput(attrs={
                'class': INPUT_CLASSES
            })
        }

    def clean_image(self):
        return validate_image_size(self.cleaned_data.get('image'))

class EditItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields =('category', 'name', 'description', 'price', 'image','is_sold')
        labels = {
            'category': 'categoría',
            'name': 'nombre',
            'description': 'descripción',
            'price': 'precio',
            'image': 'imagen',
            'is_sold': 'vendido',
        }
        widgets = {
            'category' : forms.Select(attrs={
                'class': INPUT_CLASSES
            }),
            'name' : forms.TextInput(attrs={
                'class': INPUT_CLASSES
            }),
            'description': forms.Textarea(attrs={
                'class': INPUT_CLASSES
            }),
            'price': forms.TextInput(attrs={
                'class': INPUT_CLASSES
            }),
            'image':forms.FileInput(attrs={
                'class': INPUT_CLASSES
            })
        }

    def clean_image(self):
        return validate_image_size(self.cleaned_data.get('image'))
        