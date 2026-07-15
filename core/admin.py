from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Duka, CustomUser, Category, Product, Sale, SaleItem, Order, OrderItem

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Taarifa za Duka', {'fields': ('role', 'duka')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Taarifa za Duka', {'fields': ('role', 'duka')}),
    )
    list_display = ('username', 'email', 'first_name', 'role', 'duka', 'is_staff')
    list_filter = ('role', 'duka', 'is_staff')

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'duka', 'category', 'cost_price', 'selling_price', 'stock_level')
    list_filter = ('duka', 'category')
    search_fields = ('name', 'description')

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0

class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'duka', 'cashier', 'sale_date', 'total_amount', 'payment_method')
    list_filter = ('duka', 'payment_method', 'sale_date')
    inlines = [SaleItemInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'duka', 'customer_name', 'customer_phone', 'order_date', 'total_amount', 'status')
    list_filter = ('duka', 'status', 'order_date')
    inlines = [OrderItemInline]

# Sajili models kwenye Django Admin
admin.site.register(Duka)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(Sale, SaleAdmin)
admin.site.register(Order, OrderAdmin)
