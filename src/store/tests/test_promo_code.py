from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from store.models import Order, PromoCode, PromoCodeUsage


class PromoCodeValidationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='promo_user',
            password='test-password',
        )

    def create_promo_code(self, **kwargs):
        defaults = {
            'code': 'SAVE10',
            'discount_percentage': 10,
        }
        defaults.update(kwargs)
        return PromoCode.objects.create(**defaults)

    def record_usage(self, promo_code):
        order = Order.objects.create(user=self.user)
        return PromoCodeUsage.objects.create(
            user=self.user,
            promo_code=promo_code,
            order=order,
        )

    def test_active_promo_code_is_valid(self):
        promo_code = self.create_promo_code()

        self.assertTrue(promo_code.is_valid_for_user(self.user))

    def test_expired_promo_code_becomes_inactive_and_is_invalid(self):
        promo_code = self.create_promo_code(
            expiration_date=timezone.now() - timedelta(days=1),
        )

        self.assertFalse(promo_code.is_valid_for_user(self.user))

        promo_code.refresh_from_db()
        self.assertFalse(promo_code.active)

    def test_inactive_promo_code_is_invalid(self):
        promo_code = self.create_promo_code(active=False)

        self.assertFalse(promo_code.is_valid_for_user(self.user))

    def test_promo_code_is_invalid_when_usage_limit_is_reached(self):
        promo_code = self.create_promo_code(max_uses_per_user=2)
        self.record_usage(promo_code)
        self.record_usage(promo_code)

        self.assertFalse(promo_code.is_valid_for_user(self.user))

    def test_promo_code_is_valid_when_usage_limit_is_not_reached(self):
        promo_code = self.create_promo_code(max_uses_per_user=2)
        self.record_usage(promo_code)

        self.assertTrue(promo_code.is_valid_for_user(self.user))

    def test_promo_code_with_no_usage_limit_is_valid(self):
        promo_code = self.create_promo_code(max_uses_per_user=None)
        self.record_usage(promo_code)
        self.record_usage(promo_code)

        self.assertTrue(promo_code.is_valid_for_user(self.user))
