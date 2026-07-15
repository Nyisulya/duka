from django.db import models
from django.contrib.auth.models import AbstractUser

# 1. Duka Model (Tenant)
class Duka(models.Model):
    STORE_TYPES = (
        ('sabuni', 'Wholesale Soaps (Sabuni za Jumla)'),
        ('mafuta', 'Edible Oils (Mafuta ya Kupikia)'),
        ('mixer', 'General Household / Mixer (Duka Mchanganyiko)'),
        ('vyombo', 'Kitchenware / Household Items (Vyombo na Vyombo vya Nyumbani)'),
    )

    name = models.CharField(max_length=100, verbose_name="Jina la Duka")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Duka Slug (Njia ya URL)")
    store_type = models.CharField(max_length=20, choices=STORE_TYPES, default='mixer', verbose_name="Aina ya Duka")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True, verbose_name="Nembo ya Duka")
    banner = models.ImageField(upload_to='banners/', blank=True, null=True, verbose_name="Bango la Duka (Banner)")
    theme_color = models.CharField(max_length=7, default='#2563eb', verbose_name="Rangi ya Mandhari (Theme Hex)")
    whatsapp_number = models.CharField(max_length=20, blank=True, verbose_name="Namba ya WhatsApp ya Maagizo")
    description = models.TextField(blank=True, verbose_name="Maelezo Mafupi ya Duka")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_store_type_display()})"

    class Meta:
        verbose_name = "Duka"
        verbose_name_plural = "Maduka"


# 2. Custom User Model (Kwa ajili ya Mmiliki na Wauzaji)
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('owner', 'Store Owner (Mmiliki)'),
        ('cashier', 'Cashier (Muuzaji)'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='cashier', verbose_name="Jukumu")
    duka = models.ForeignKey(Duka, on_delete=models.CASCADE, null=True, blank=True, related_name="users", verbose_name="Duka analofanyia kazi")

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# 3. Category Model
class Category(models.Model):
    duka = models.ForeignKey(Duka, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=50, verbose_name="Jina la Kategoria")

    class Meta:
        verbose_name = "Kategoria"
        verbose_name_plural = "Kategoria"
        unique_together = ('duka', 'name')

    def __str__(self):
        return f"{self.name} - {self.duka.name}"


# 4. Product Model
class Product(models.Model):
    duka = models.ForeignKey(Duka, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    name = models.CharField(max_length=100, verbose_name="Jina la Bidhaa")
    description = models.TextField(blank=True, verbose_name="Maelezo ya Bidhaa")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Picha ya Bidhaa")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Bei ya Kununulia (Cost Price)")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Bei ya Kuuzia (Selling Price)")
    stock_level = models.IntegerField(default=0, verbose_name="Kiasi Kilichopo Stoo")
    min_stock_alert = models.IntegerField(default=5, verbose_name="Kiwango cha Kutoa Taarifa (Reorder Alert)")

    def __str__(self):
        return f"{self.name} ({self.duka.name})"

    @property
    def is_low_stock(self):
        return self.stock_level <= self.min_stock_alert


# 5. Sale Model (Mauzo ya Duka la POS)
class Sale(models.Model):
    PAYMENT_METHODS = (
        ('cash', 'Cash (Fedha Taslimu)'),
        ('m-pesa', 'M-Pesa'),
        ('tigopesa', 'Tigo Pesa'),
        ('airtelmoney', 'Airtel Money'),
        ('halo-pesa', 'Halo Pesa'),
        ('card', 'Bank Card / Visa'),
    )

    duka = models.ForeignKey(Duka, on_delete=models.CASCADE, related_name="sales")
    cashier = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="sales")
    sale_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')

    def __str__(self):
        return f"Mauzo #{self.id} - {self.duka.name} ({self.sale_date.strftime('%d/%m/%Y %H:%M')})"


# 6. SaleItem Model
class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Bei Wakati wa Mauzo")

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def subtotal(self):
        return self.quantity * self.price_at_sale


# 7. Order Model (Maagizo ya Mtandaoni - E-commerce Orders)
class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending (Kusubiri)'),
        ('completed', 'Completed (Tayari)'),
        ('cancelled', 'Cancelled (Kufutwa)'),
    )

    duka = models.ForeignKey(Duka, on_delete=models.CASCADE, related_name="orders")
    customer_name = models.CharField(max_length=100, verbose_name="Jina la Mteja")
    customer_phone = models.CharField(max_length=20, verbose_name="Namba ya Simu")
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Agizo #{self.id} - {self.customer_name} ({self.duka.name})"


# 8. OrderItem Model
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price_at_order = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Bei Wakati wa Kuagiza")

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def subtotal(self):
        return self.quantity * self.price_at_order
