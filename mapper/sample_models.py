from django.db import models

class Product(models.Model):
    """Sample Product model for testing"""
    name = models.CharField(max_length=200, help_text="Product name")
    sku = models.CharField(max_length=50, unique=True, help_text="Stock keeping unit")
    description = models.TextField(blank=True, help_text="Product description")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Product price")
    quantity = models.IntegerField(default=0, help_text="Available quantity")
    category = models.CharField(max_length=100, blank=True, help_text="Product category")
    is_active = models.BooleanField(default=True, help_text="Is product active?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
    
    def __str__(self):
        return self.name


class Customer(models.Model):
    """Sample Customer model for testing"""
    first_name = models.CharField(max_length=100, help_text="First name")
    last_name = models.CharField(max_length=100, help_text="Last name")
    email = models.EmailField(unique=True, help_text="Email address")
    phone = models.CharField(max_length=20, blank=True, help_text="Phone number")
    address = models.TextField(blank=True, help_text="Street address")
    city = models.CharField(max_length=100, blank=True, help_text="City")
    country = models.CharField(max_length=100, blank=True, help_text="Country")
    zip_code = models.CharField(max_length=20, blank=True, help_text="ZIP/Postal code")
    date_joined = models.DateField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
