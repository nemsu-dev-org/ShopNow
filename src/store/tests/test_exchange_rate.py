from decimal import Decimal

from django.conf import settings
from django.test import TestCase, override_settings

from store.models import Category, Product


class ExchangeRateTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Gadgets')

    def test_default_rate_keeps_displayed_prices_unchanged(self):
        self.assertEqual(settings.USD_TO_PHP_RATE, Decimal('59.41'))
        product = Product.objects.create(name='Mug', category=self.category, price=Decimal('10.00'))

        self.assertEqual(product.price_in_peso, '₱594.10')

    @override_settings(USD_TO_PHP_RATE=Decimal('50.00'))
    def test_peso_price_uses_the_rate_from_settings(self):
        product = Product.objects.create(name='Mug', category=self.category, price=Decimal('10.00'))

        self.assertEqual(product.price_in_peso_value, Decimal('500.00'))
        self.assertEqual(product.discounted_price, Decimal('500.00'))
