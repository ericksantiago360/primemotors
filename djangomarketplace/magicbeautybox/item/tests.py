import io
import os
import shutil
import tempfile
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .forms import MAX_IMAGE_BYTES, NewItemForm, validate_image_size
from .models import category, Item


class ItemViewsTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('owner', password='pass12345')
        self.other = User.objects.create_user('other', password='pass12345')
        self.category = category.objects.create(name='Sedan')
        self.item = Item.objects.create(category=self.category, name='Civic', price=100, created_by=self.owner)

    def test_pages_render_items_without_image(self):
        for url in [reverse('core:index'), reverse('item:items'), reverse('item:detail', args=[self.item.pk])]:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_index_counts_only_unsold_items_per_category(self):
        Item.objects.create(category=self.category, name='Vendido', price=100, created_by=self.owner, is_sold=True)

        response = self.client.get(reverse('core:index'))

        self.assertContains(response, '1 artículos')
        self.assertNotContains(response, '2 artículos')

    def test_items_invalid_category_does_not_crash(self):
        response = self.client.get(reverse('item:items'), {'category': 'abc'})
        self.assertEqual(response.status_code, 200)

    def test_delete_requires_post(self):
        self.client.login(username='owner', password='pass12345')
        response = self.client.get(reverse('item:delete', args=[self.item.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Item.objects.filter(pk=self.item.pk).exists())

        self.client.post(reverse('item:delete', args=[self.item.pk]))
        self.assertFalse(Item.objects.filter(pk=self.item.pk).exists())

    def test_sold_item_shows_badge_and_hides_contact_seller(self):
        self.item.is_sold = True
        self.item.save()
        self.client.login(username='other', password='pass12345')

        response = self.client.get(reverse('item:detail', args=[self.item.pk]))

        self.assertContains(response, 'vendido')
        self.assertNotContains(response, reverse('conversation:new', args=[self.item.pk]))

    def test_available_item_shows_contact_seller(self):
        self.client.login(username='other', password='pass12345')

        response = self.client.get(reverse('item:detail', args=[self.item.pk]))

        self.assertNotContains(response, 'vendido')
        self.assertContains(response, reverse('conversation:new', args=[self.item.pk]))

    def test_owner_can_change_category_when_editing(self):
        other_cat = category.objects.create(name='SUV')
        self.client.login(username='owner', password='pass12345')
        url = reverse('item:edit', args=[self.item.pk])

        self.assertContains(self.client.get(url), f'<option value="{other_cat.pk}">SUV</option>')
        self.client.post(url, {
            'category': other_cat.pk,
            'name': 'Civic',
            'description': '',
            'price': '100',
            'is_sold': '',
        })

        self.item.refresh_from_db()
        self.assertEqual(self.item.category, other_cat)

    def test_cannot_delete_other_users_item(self):
        self.client.login(username='other', password='pass12345')
        response = self.client.post(reverse('item:delete', args=[self.item.pk]))
        self.assertEqual(response.status_code, 404)


class ItemListPaginationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('owner', password='pass12345')
        self.sedan = category.objects.create(name='Sedan')
        self.suv = category.objects.create(name='SUV')
        for i in range(13):
            Item.objects.create(category=self.sedan, name=f'Sedan {i}', price=100, created_by=self.owner)

    def test_lists_twelve_items_per_page(self):
        self.assertEqual(len(self.client.get(reverse('item:items')).context['items']), 12)
        self.assertEqual(len(self.client.get(reverse('item:items'), {'page': 2}).context['items']), 1)

    def test_page_links_keep_query_and_category(self):
        response = self.client.get(reverse('item:items'), {'query': 'sedan', 'category': self.sedan.pk})

        self.assertContains(response, f'?query=sedan&amp;category={self.sedan.pk}&amp;page=2')

    def test_invalid_page_does_not_crash(self):
        response = self.client.get(reverse('item:items'), {'page': 'abc'})

        self.assertEqual(response.status_code, 200)

    def test_empty_category_has_no_items(self):
        response = self.client.get(reverse('item:items'), {'category': self.suv.pk})

        self.assertEqual(len(response.context['items']), 0)


class ItemImageSizeTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('owner', password='pass12345')
        self.category = category.objects.create(name='Sedan')

    def form_data(self):
        return {'category': self.category.pk, 'name': 'Civic', 'description': '', 'price': '100'}

    def test_validator_rejects_image_over_5_mb(self):
        big = SimpleUploadedFile('grande.jpg', b'0' * (MAX_IMAGE_BYTES + 1), content_type='image/jpeg')

        with self.assertRaises(ValidationError):
            validate_image_size(big)

    def test_validator_accepts_image_at_5_mb(self):
        ok = SimpleUploadedFile('ok.jpg', b'0' * MAX_IMAGE_BYTES, content_type='image/jpeg')

        self.assertIs(validate_image_size(ok), ok)

    def test_form_rejects_real_image_over_5_mb(self):
        buf = io.BytesIO()
        Image.new('RGB', (4, 4)).save(buf, 'PNG')
        # PNG válido; el relleno tras IEND lo hace pesar más de 5 MB
        heavy = SimpleUploadedFile('pesada.png', buf.getvalue() + b'\0' * MAX_IMAGE_BYTES, content_type='image/png')

        form = NewItemForm(data=self.form_data(), files={'image': heavy})

        self.assertFalse(form.is_valid())
        self.assertIn('5 MB', str(form.errors['image']))


class ItemPriceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('owner', password='pass12345')
        self.category = category.objects.create(name='Sedan')

    def test_negative_price_is_rejected_by_model_validation(self):
        item = Item(category=self.category, name='Civic', price=Decimal('-1'), created_by=self.owner)

        with self.assertRaises(ValidationError) as ctx:
            item.full_clean()

        self.assertIn('price', ctx.exception.message_dict)

    def test_zero_price_is_allowed(self):
        item = Item(category=self.category, name='Civic', price=Decimal('0'), created_by=self.owner)

        item.full_clean()

    def test_new_item_form_rejects_negative_price(self):
        form = NewItemForm(data={
            'category': self.category.pk,
            'name': 'Civic',
            'description': '',
            'price': '-500',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)


class ItemImageFileTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()
        self.owner = User.objects.create_user('owner', password='pass12345')
        self.category = category.objects.create(name='Sedan')

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def make_item(self, filename):
        image = SimpleUploadedFile(filename, b'contenido', content_type='image/jpeg')
        return Item.objects.create(category=self.category, name='Civic', price=100, created_by=self.owner, image=image)

    def file_exists(self, name):
        return os.path.exists(os.path.join(self.media_root, name))

    def test_deleting_item_removes_image_file(self):
        item = self.make_item('auto.jpg')
        path = item.image.name
        self.assertTrue(self.file_exists(path))

        item.delete()

        self.assertFalse(self.file_exists(path))

    def test_replacing_image_removes_old_file(self):
        item = self.make_item('viejo.jpg')
        old_path = item.image.name

        item.image = SimpleUploadedFile('nuevo.jpg', b'otro', content_type='image/jpeg')
        item.save()

        self.assertFalse(self.file_exists(old_path))
        self.assertTrue(self.file_exists(item.image.name))

    def test_saving_without_changing_image_keeps_file(self):
        item = self.make_item('igual.jpg')
        path = item.image.name

        item.name = 'Accord'
        item.save()

        self.assertTrue(self.file_exists(path))
