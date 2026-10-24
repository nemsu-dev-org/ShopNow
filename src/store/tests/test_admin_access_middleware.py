from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AdminAccessMiddlewareTests(TestCase):
    def setUp(self):
        self.admin_url = reverse('admin:index')
        self.user = get_user_model().objects.create_user(
            username='regular_user',
            password='test-password',
        )
        self.staff_user = get_user_model().objects.create_user(
            username='staff_user',
            password='test-password',
            is_staff=True,
        )

    def test_anonymous_user_sees_access_denied_page(self):
        response = self.client.get(self.admin_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'store/authentication-page/admin_access_denied.html',
        )
        self.assertContains(response, 'Access Denied')

    def test_non_staff_user_sees_access_denied_page(self):
        self.client.force_login(self.user)

        response = self.client.get(self.admin_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'store/authentication-page/admin_access_denied.html',
        )
        self.assertContains(response, 'Access Denied')

    def test_staff_user_can_access_admin(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(self.admin_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/index.html')
        self.assertNotContains(response, 'Access Denied')
