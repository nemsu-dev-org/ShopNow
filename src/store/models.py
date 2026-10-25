from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth.models import User
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Avg, Count
from django.utils import timezone
from django.conf import settings
from django.db import models
import secrets
import uuid
from django.utils import timezone
import random
from datetime import timedelta
from django.utils.crypto import get_random_string


def generate_payment_id():
    return secrets.token_hex(16)


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.URLField(max_length=500, blank=True, null=True)
    additional_images = models.JSONField(blank=True, null=True)

    is_featured = models.BooleanField(default=False)
    discount_percentage = models.PositiveIntegerField(default=0)
    buyers_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name
    
    @property
    def price_in_peso_value(self):
        usd_to_php = settings.USD_TO_PHP_RATE
        return (self.price * usd_to_php).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def price_in_peso(self):
        formatted_price = f"{self.price_in_peso_value:,}"
        return f"₱{formatted_price}"

    @property
    def discounted_price(self):
        price_in_peso = self.price_in_peso_value  # Use numeric value
        if self.is_on_sale:
            discounted = price_in_peso * (Decimal(1) - Decimal(self.discount_percentage) / Decimal(100))
            return discounted.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return price_in_peso
    
    @property
    def is_on_sale(self):
        return self.discount_percentage > 0

    @property
    def buyers_count_display(self):
        count = self.buyers_count
        if count >= 1_000_000:
            return f"{count / 1_000_000:.1f}M"
        elif count >= 1_000:
            return f"{count / 1_000:.1f}K"
        return str(count)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @property
    def review_count(self):
        return self.reviews.aggregate(count=Count("id"))["count"] or 0

    @property
    def average_ratings(self):
        return self.reviews.aggregate(Avg("rating"))["rating__avg"] or 0


class PromoCodeUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    promo_code = models.ForeignKey("PromoCode", on_delete=models.CASCADE)
    order = models.ForeignKey("Order", null=True, blank=True, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "promo_code", "order")


class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percentage = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    active = models.BooleanField(default=True)
    expiration_date = models.DateTimeField(null=True, blank=True)
    max_uses_per_user = models.PositiveIntegerField(
        null=True, blank=True
    )  # Null = unlimited per user

    def is_valid_for_user(self, user):
        if self.expiration_date and self.expiration_date <= timezone.now():
            self.active = False
            self.save(update_fields=["active"])
            return False

        # Count user uses
        used_count = PromoCodeUsage.objects.filter(
            user=user, promo_code=self, order__isnull=False
        ).count()

        if self.max_uses_per_user is not None and used_count >= self.max_uses_per_user:
            return False

        return self.active


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")

    @property
    def get_total(self):
        return self.product.discounted_price * self.quantity


class Order(models.Model):
    # your fields...
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("SHIPPED", "Shipped"),
        ("DELIVERED", "Delivered"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")

    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    promo_code = models.ForeignKey(
        PromoCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    last_status_update = models.DateTimeField(auto_now_add=True)
    next_status_update = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username} - {self.status}"

    @property
    def subtotal(self):
        return self.total_price - self.shipping_price + self.discount

    def generate_next_update_time(self):
        # Random 5 to 15 minutes after last update
        minutes = random.randint(5, 15)
        self.next_status_update = timezone.now() + timedelta(minutes=minutes)
        self.save()

    def advance_status(self):
        status_flow = ["PENDING", "PROCESSING", "SHIPPED", "DELIVERED"]
        try:
            next_index = status_flow.index(self.status) + 1
            if next_index < len(status_flow):
                self.status = status_flow[next_index]
                self.last_status_update = timezone.now()
                self.generate_next_update_time()
                self.save()
        except ValueError:
            pass  # Status not recognized or already at the last status


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_items"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=20, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x{self.quantity} for Order #{self.order.id}"


class PaymentMethod(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payment_methods",
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    payment_id = models.CharField(
        max_length=100,
        unique=True,
        default=generate_payment_id,
        primary_key=True,
        editable=False,
    )

    payment_method = models.CharField(
        max_length=20,
        choices=[
            ("gcash", "GCash"),
            ("paypal", "PayPal"),
        ],
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Not in used

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"

    def __str__(self):
        return f"{self.get_payment_method_display()} ({self.payment_id})"


class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reset_id = models.UUIDField(default=uuid.uuid4, unique=True)
    code = models.CharField(max_length=6, blank=True)  # 6-digit code for example
    created_when = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = get_random_string(length=6, allowed_chars='0123456789')
        super().save(*args, **kwargs)


class ShippingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    user_profile = models.ImageField(upload_to="images/", blank=True, null=True)

    def __str__(self):
        return f"{self.address}, {self.country} - {self.user}"


class ProductReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")

    def __str__(self):
        return f"Review by {self.user.username} for {self.product.name}"


class ProductWishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")


class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
