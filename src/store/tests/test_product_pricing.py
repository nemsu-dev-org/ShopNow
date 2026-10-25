from decimal import Decimal

from django.test import TestCase

from store.models import Category, Product


class ProductPricingTests(TestCase):
    """Peso conversion (1 USD = 59.41 PHP), discounts, rounding and the buyers count display."""

    def setUp(self):
        self.category = Category.objects.create(name='Gadgets')

    def create_product(self, **kwargs):
        defaults = {
            'name': 'Test Product',
            'category': self.category,
            'price': Decimal('10.00'),
        }
        defaults.update(kwargs)
        return Product.objects.create(**defaults)

    def test_price_is_converted_to_pesos(self):
        product = self.create_product(price=Decimal('10.00'))

        self.assertEqual(product.price_in_peso_value, Decimal('594.10'))
        self.assertEqual(product.price_in_peso, '₱594.10')

    def test_peso_price_uses_a_thousands_separator(self):
        product = self.create_product(price=Decimal('100.00'))

        self.assertEqual(product.price_in_peso, '₱5,941.00')

    def test_peso_price_rounds_to_two_decimals_half_up(self):
        # 0.01 * 59.41 = 0.5941 rounds down; 0.55 * 59.41 = 32.6755 rounds up
        self.assertEqual(self.create_product(price=Decimal('0.01')).price_in_peso_value, Decimal('0.59'))
        self.assertEqual(self.create_product(price=Decimal('0.55')).price_in_peso_value, Decimal('32.68'))

    def test_without_a_discount_the_product_is_not_on_sale(self):
        product = self.create_product(price=Decimal('10.00'))

        self.assertFalse(product.is_on_sale)
        self.assertEqual(product.discounted_price, product.price_in_peso_value)

    def test_discount_is_taken_off_the_peso_price(self):
        product = self.create_product(price=Decimal('10.00'), discount_percentage=20)

        self.assertTrue(product.is_on_sale)
        # 594.10 * 0.80
        self.assertEqual(product.discounted_price, Decimal('475.28'))

    def test_discounted_price_rounds_half_up(self):
        # 59.41 * 0.85 = 50.4985, which rounds up to 50.50
        product = self.create_product(price=Decimal('1.00'), discount_percentage=15)

        self.assertEqual(product.discounted_price, Decimal('50.50'))

    def test_full_discount_makes_the_product_free(self):
        product = self.create_product(price=Decimal('10.00'), discount_percentage=100)

        self.assertEqual(product.discounted_price, Decimal('0.00'))

    def test_buyers_count_below_a_thousand_is_shown_as_is(self):
        for count, shown in ((0, '0'), (1, '1'), (999, '999')):
            with self.subTest(count=count):
                product = self.create_product(buyers_count=count)
                self.assertEqual(product.buyers_count_display, shown)

    def test_buyers_count_in_thousands_uses_k(self):
        for count, shown in ((1_000, '1.0K'), (1_500, '1.5K'), (25_340, '25.3K')):
            with self.subTest(count=count):
                product = self.create_product(buyers_count=count)
                self.assertEqual(product.buyers_count_display, shown)

    def test_buyers_count_in_millions_uses_m(self):
        for count, shown in ((1_000_000, '1.0M'), (2_500_000, '2.5M')):
            with self.subTest(count=count):
                product = self.create_product(buyers_count=count)
                self.assertEqual(product.buyers_count_display, shown)
