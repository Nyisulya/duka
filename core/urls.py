from django.urls import path
from . import views

urlpatterns = [
    # 1. Platform Main Domain URLs (SaaS level)
    path('', views.index, name='index'),  # Njia kuu ya tovuti (inaamua kama ni duka au platform landing)
    path('register/', views.register_duka, name='register_duka'),  # Kusajili duka jipya
    
    # 2. Tovuti ya Mbele ya kila Duka (Customer Shopfront - Slug-based)
    path('store/<slug:slug>/', views.store_home, name='store_home_slug'),
    path('store/<slug:slug>/cart/', views.store_cart, name='store_cart_slug'),
    path('store/<slug:slug>/checkout/', views.store_checkout, name='store_checkout_slug'),
    path('store/<slug:slug>/order-success/<int:order_id>/', views.store_order_success, name='store_order_success_slug'),
    
    # 3. Sehemu ya Utawala (Admin Panel) na POS kwa kila Duka
    path('store/<slug:slug>/admin/login/', views.store_login, name='store_login_slug'),
    path('store/<slug:slug>/admin/logout/', views.store_logout, name='store_logout_slug'),
    
    path('store/<slug:slug>/admin/dashboard/', views.store_admin_dashboard, name='store_admin_dashboard_slug'),
    path('store/<slug:slug>/admin/products/', views.store_products, name='store_products_slug'),
    path('store/<slug:slug>/admin/products/add/', views.store_product_add, name='store_product_add_slug'),
    path('store/<slug:slug>/admin/products/<int:product_id>/edit/', views.store_product_edit, name='store_product_edit_slug'),
    path('store/<slug:slug>/admin/categories/', views.store_categories, name='store_categories_slug'),
    path('store/<slug:slug>/admin/settings/', views.store_settings, name='store_settings_slug'),
    path('store/<slug:slug>/admin/sales/', views.store_sales_report, name='store_sales_report_slug'),
    path('store/<slug:slug>/admin/debts/', views.store_debts, name='store_debts_slug'),
    path('store/<slug:slug>/admin/debts/<int:customer_id>/', views.store_debt_detail, name='store_debt_detail_slug'),
    path('store/<slug:slug>/admin/debts/<int:customer_id>/pay/', views.store_debt_pay, name='store_debt_pay_slug'),
    
    # 4. Point of Sale (POS) & Orders
    path('store/<slug:slug>/admin/pos/', views.store_pos, name='store_pos_slug'),
    path('store/<slug:slug>/admin/pos/checkout/', views.store_pos_checkout, name='store_pos_checkout_slug'),
    path('store/<slug:slug>/admin/customers/quick-add/', views.store_quick_customer, name='store_quick_customer_slug'),
    path('store/<slug:slug>/admin/orders/', views.store_orders, name='store_orders_slug'),
    path('store/<slug:slug>/admin/orders/<int:order_id>/update/', views.store_order_update, name='store_order_update_slug'),
]
