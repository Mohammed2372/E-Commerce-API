from django.db import models
from django.utils.text import slugify
from django.conf import settings


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = slugify(name)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.ManyToManyField(Category, related_name="products")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # image = models.ImageField(upload_to="static/products/")
    in_stock = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Cart(models.Model):
    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Paid", "Paid (Order History)"),
        # ("Cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="carts"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Active")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_price(self):
        total = sum(item.subtotal for item in self.items.all())
        return (total, 2)

    def __str__(self):
        return f"Cart for {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.quantity * self.product.price

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    class Meta:
        unique_together = ("cart", "product")
