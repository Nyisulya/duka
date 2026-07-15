import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404, HttpResponse
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.utils.text import slugify
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import urllib.parse

from .models import Duka, CustomUser, Category, Product, Sale, SaleItem, Order, OrderItem

# Helper decorator ili kuhakikisha mtumiaji aliye-login anafikia duka lake tu
def store_access_required(view_func):
    def wrapper(request, slug, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('store_login_slug', slug=slug)
        
        # Superuser ana access kila mahali. Wengine lazima duka lifanane.
        if not request.user.is_superuser:
            if not request.user.duka or request.user.duka.slug != slug:
                messages.error(request, "Huna ruhusa ya kufikia duka hili.")
                return redirect('index')
                
        return view_func(request, slug, *args, **kwargs)
    return wrapper

# 1. Main Index View
def index(request):
    """
    Kama duka limetambuliwa kupitia subdomain, inampeleka mteja kwenye duka husika.
    Vinginevyo, inaonyesha ukurasa mkuu wa mfumo wa SaaS wa kujisajili.
    """
    if getattr(request, 'duka', None):
        return store_home(request, slug=request.duka.slug)
    
    # Kama tupo kwenye domain kuu, tuonyeshe maduka yaliyopo pia
    maduka = Duka.objects.all().order_by('-created_at')[:6]
    return render(request, 'platform/landing.html', {'maduka': maduka})


# 2. Register Duka View (SaaS level)
def register_duka(request):
    if request.method == 'POST':
        duka_name = request.POST.get('duka_name')
        store_type = request.POST.get('store_type', 'mixer')
        owner_name = request.POST.get('owner_name')
        owner_email = request.POST.get('owner_email')
        password = request.POST.get('password')
        whatsapp_number = request.POST.get('whatsapp_number', '')

        slug = slugify(duka_name)
        
        # Kuhakikisha slug ni ya kipekee
        if Duka.objects.filter(slug=slug).exists():
            messages.error(request, f"Duka lenye jina '{duka_name}' tayari lipo. Tafadhali chagua jina lingine kidogo.")
            return render(request, 'platform/register.html')
            
        if CustomUser.objects.filter(username=owner_email).exists():
            messages.error(request, f"Barua pepe '{owner_email}' tayari imetumika.")
            return render(request, 'platform/register.html')

        # Unda Duka
        duka = Duka.objects.create(
            name=duka_name,
            slug=slug,
            store_type=store_type,
            whatsapp_number=whatsapp_number
        )

        # Unda Owner CustomUser
        user = CustomUser.objects.create_user(
            username=owner_email,
            email=owner_email,
            password=password,
            first_name=owner_name,
            role='owner',
            duka=duka
        )

        # Weka Kategoria za kwanza kiotomatiki kutegemeana na aina ya duka
        if store_type == 'sabuni':
            Category.objects.bulk_create([
                Category(duka=duka, name="Sabuni za Kufulia"),
                Category(duka=duka, name="Sabuni za Kuogea"),
                Category(duka=duka, name="Sabuni za Maji / Usafi"),
            ])
        elif store_type == 'mafuta':
            Category.objects.bulk_create([
                Category(duka=duka, name="Mafuta ya Alizeti"),
                Category(duka=duka, name="Mafuta ya Mawese"),
                Category(duka=duka, name="Mafuta ya Nazi"),
            ])
        else:
            Category.objects.bulk_create([
                Category(duka=duka, name="Usafi & Sabuni"),
                Category(duka=duka, name="Mafuta ya Kupikia"),
                Category(duka=duka, name="Vyombo & Vifaa"),
            ])

        # Login user
        login(request, user)
        messages.success(request, f"Duka lako la '{duka_name}' limesajiliwa kikamilifu!")
        return redirect('store_admin_dashboard_slug', slug=slug)

    return render(request, 'platform/register.html')


# 3. Store Front-End E-commerce views
def store_home(request, slug):
    # Kama middleware haijapata duka, tafuta hapa
    duka = getattr(request, 'duka', None)
    if not duka or duka.slug != slug:
        duka = get_object_or_404(Duka, slug=slug)

    categories = duka.categories.all()
    products = duka.products.all()
    
    # Filter kwa kategoria
    selected_cat = request.GET.get('category')
    if selected_cat:
        products = products.filter(category_id=selected_cat)

    # Search bidhaa
    query = request.GET.get('q')
    if query:
        products = products.filter(name__icontains=query)

    context = {
        'duka': duka,
        'categories': categories,
        'products': products,
        'selected_cat': selected_cat,
        'q': query,
    }
    return render(request, 'store/home.html', context)


def store_cart(request, slug):
    duka = get_object_or_404(Duka, slug=slug)
    return render(request, 'store/cart.html', {'duka': duka})


def store_checkout(request, slug):
    duka = get_object_or_404(Duka, slug=slug)
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name')
        customer_phone = request.POST.get('customer_phone')
        cart_data_raw = request.POST.get('cart_data')  # Imepokelewa kama JSON string kutoka local storage
        
        try:
            cart_data = json.loads(cart_data_raw)
        except (TypeError, json.JSONDecodeError):
            messages.error(request, "Kulikuwa na hitilafu katika kikapu chako.")
            return redirect('store_cart_slug', slug=slug)

        if not cart_data:
            messages.error(request, "Kikapu chako kipo tupu.")
            return redirect('store_cart_slug', slug=slug)

        # Tengeneza Order
        order = Order.objects.create(
            duka=duka,
            customer_name=customer_name,
            customer_phone=customer_phone,
            total_amount=0
        )

        total = 0
        whatsapp_message_items = []

        for item in cart_data:
            product = get_object_or_404(Product, id=item['id'], duka=duka)
            qty = int(item['quantity'])
            price = product.selling_price
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=qty,
                price_at_order=price
            )
            total += qty * price
            whatsapp_message_items.append(f"- {product.name} x{qty} (@ {price:,.0f} Tsh) = {qty*price:,.0f} Tsh")

        order.total_amount = total
        order.save()

        # Kupunguza stoo kwa maagizo ya mtandaoni kiotomatiki
        for item in cart_data:
            product = Product.objects.filter(id=item['id'], duka=duka).first()
            if product:
                product.stock_level = max(0, product.stock_level - int(item['quantity']))
                product.save()

        # Kuandaa meseji ya WhatsApp
        whatsapp_msg = (
            f"Habari *{duka.name}*, naitwa *{customer_name}* (Simu: {customer_phone}).\n"
            f"Naomba kuagiza bidhaa zifuatazo kupitia tovuti yenu:\n\n"
            + "\n".join(whatsapp_message_items) + "\n\n"
            f"*Jumla Kuu: {total:,.0f} Tsh*\n\n"
            f"Namba ya agizo kwenye mfumo: #{order.id}."
        )

        # Format number kwa usahihi kwa ajili ya WhatsApp Link
        clean_phone = duka.whatsapp_number.replace('+', '').replace(' ', '')
        if clean_phone.startswith('0'):
            clean_phone = '255' + clean_phone[1:]  # Default kwa Tanzania
            
        whatsapp_url = f"https://wa.me/{clean_phone}?text={urllib.parse.quote(whatsapp_msg)}"
        
        request.session[f'order_success_{order.id}'] = True
        
        # Tuma redirect na WhatsApp URL
        return render(request, 'store/redirect_whatsapp.html', {
            'whatsapp_url': whatsapp_url,
            'success_url': request.build_absolute_uri(f'/store/{slug}/order-success/{order.id}/')
        })

    return render(request, 'store/checkout.html', {'duka': duka})


def store_order_success(request, slug, order_id):
    duka = get_object_or_404(Duka, slug=slug)
    order = get_object_or_404(Order, id=order_id, duka=duka)
    return render(request, 'store/order_success.html', {'duka': duka, 'order': order})


# 4. Store Administration Views
def store_login(request, slug):
    duka = get_object_or_404(Duka, slug=slug)
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        if user is not None:
            # Hakikisha mfanyakazi huyu ni wa duka hili au ni superuser
            if user.is_superuser or (user.duka and user.duka.slug == slug):
                login(request, user)
                messages.success(request, f"Karibu tena, {user.first_name}!")
                return redirect('store_admin_dashboard_slug', slug=slug)
            else:
                messages.error(request, "Akaunti hii haina ruhusa ya kuingia kwenye duka hili.")
        else:
            messages.error(request, "Barua pepe au nenosiri si sahihi.")
            
    return render(request, 'store/admin/login.html', {'duka': duka})


def store_logout(request, slug):
    logout(request)
    return redirect('store_login_slug', slug=slug)


@login_required
@store_access_required
def store_admin_dashboard(request, slug):
    duka = request.user.duka if not request.user.is_superuser else get_object_or_404(Duka, slug=slug)
    
    # Takwimu za Jumla
    total_sales = Sale.objects.filter(duka=duka).aggregate(sum=Sum('total_amount'))['sum'] or 0
    total_orders = Order.objects.filter(duka=duka).count()
    low_stock_products = Product.objects.filter(duka=duka, stock_level__lte=F('min_stock_alert'))
    
    # Graph ya Mauzo ya Siku 7 zilizopita
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_sales = Sale.objects.filter(duka=duka, sale_date__gte=seven_days_ago)
    
    # Hivi majuzi mauzo na maagizo
    latest_sales = Sale.objects.filter(duka=duka).order_by('-sale_date')[:5]
    latest_orders = Order.objects.filter(duka=duka).order_by('-order_date')[:5]

    context = {
        'duka': duka,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'low_stock_count': low_stock_products.count(),
        'low_stock_products': low_stock_products[:5],
        'latest_sales': latest_sales,
        'latest_orders': latest_orders,
    }
    return render(request, 'store/admin/dashboard.html', context)


@login_required
@store_access_required
def store_products(request, slug):
    duka = request.user.duka if not request.user.is_superuser else get_object_or_404(Duka, slug=slug)
    products = duka.products.all().order_by('name')
    return render(request, 'store/admin/products.html', {'duka': duka, 'products': products})


@login_required
@store_access_required
def store_product_add(request, slug):
    duka = request.user.duka if not request.user.is_superuser else get_object_or_404(Duka, slug=slug)
    categories = duka.categories.all()
    
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description', '')
        cost_price = request.POST.get('cost_price', 0)
        selling_price = request.POST.get('selling_price', 0)
        stock_level = request.POST.get('stock_level', 0)
        min_stock_alert = request.POST.get('min_stock_alert', 5)
        image = request.FILES.get('image')

        category = Category.objects.filter(id=category_id, duka=duka).first() if category_id else None

        Product.objects.create(
            duka=duka,
            category=category,
            name=name,
            description=description,
            cost_price=cost_price,
            selling_price=selling_price,
            stock_level=stock_level,
            min_stock_alert=min_stock_alert,
            image=image
        )
        messages.success(request, f"Bidhaa '{name}' imeongezwa kikamilifu!")
        return redirect('store_products_slug', slug=slug)

    return render(request, 'store/admin/product_form.html', {'duka': duka, 'categories': categories})


@login_required
@store_access_required
def store_product_edit(request, slug, product_id):
    duka = request.user.duka if not request.user.is_superuser else get_object_or_404(Duka, slug=slug)
    product = get_object_or_404(Product, id=product_id, duka=duka)
    categories = duka.categories.all()

    if request.method == 'POST':
        product.name = request.POST.get('name')
        category_id = request.POST.get('category')
        product.description = request.POST.get('description', '')
        product.cost_price = request.POST.get('cost_price', 0)
        product.selling_price = request.POST.get('selling_price', 0)
        product.stock_level = request.POST.get('stock_level', 0)
        product.min_stock_alert = request.POST.get('min_stock_alert', 5)
        
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')

        product.category = Category.objects.filter(id=category_id, duka=duka).first() if category_id else None
        product.save()
        
        messages.success(request, f"Bidhaa '{product.name}' imesasishwa!")
        return redirect('store_products_slug', slug=slug)

    return render(request, 'store/admin/product_form.html', {'duka': duka, 'product': product, 'categories': categories})


@login_required
@store_access_required
def store_categories(request, slug):
    duka = request.user.duka if not request.user.is_superuser else get_object_or_404(Duka, slug=slug)
    categories = duka.categories.all()
    
    if request.method == 'POST':
        # Add category
        name = request.POST.get('name')
        if name:
            if not Category.objects.filter(duka=duka, name__iexact=name).exists():
                Category.objects.create(duka=duka, name=name)
                messages.success(request, f"Kategoria '{name}' imeundwa!")
            else:
                messages.warning(request, "Kategoria hii tayari ipo.")
        return redirect('store_categories_slug', slug=slug)

    # Delete handling via GET request parameters
    delete_id = request.GET.get('delete')
    if delete_id:
        category = Category.objects.filter(id=delete_id, duka=duka).first()
        if category:
            category.delete()
            messages.success(request, "Kategoria imefutwa.")
        return redirect('store_categories_slug', slug=slug)

    return render(request, 'store/admin/categories.html', {'duka': duka, 'categories': categories})


@login_required
@store_access_required
def store_settings(request, slug):
    duka = request.user.duka if not request.user.is_superuser else get_object_or_404(Duka, slug=slug)
    
    if request.method == 'POST':
        duka.name = request.POST.get('name')
        duka.whatsapp_number = request.POST.get('whatsapp_number', '')
        duka.theme_color = request.POST.get('theme_color', '#2563eb')
        duka.description = request.POST.get('description', '')
        
        if request.FILES.get('logo'):
            duka.logo = request.FILES.get('logo')
        if request.FILES.get('banner'):
            duka.banner = request.FILES.get('banner')
            
        duka.save()
        messages.success(request, "Mipangilio ya duka imesasishwa kikamilifu!")
        return redirect('store_settings_slug', slug=slug)

    return render(request, 'store/admin/settings.html', {'duka': duka})


# 5. Point of Sale (POS) View
@login_required
@store_access_required
def store_pos(request, slug):
    duka = request.user.duka if not request.user.is_superuser else get_object_or_404(Duka, slug=slug)
    products = duka.products.filter(stock_level__gt=0).order_by('name')
    categories = duka.categories.all()
    
    # JSON product data for POS frontend logic
    pos_products = []
    for p in products:
        pos_products.append({
            'id': p.id,
            'name': p.name,
            'price': float(p.selling_price),
            'stock': p.stock_level,
            'image': p.image.url if p.image else '',
            'category_id': p.category.id if p.category else None
        })

    context = {
        'duka': duka,
        'categories': categories,
        'products_json': json.dumps(pos_products),
    }
    return render(request, 'store/admin/pos.html', context)


@login_required
@store_access_required
def store_pos_checkout(request, slug):
    duka = request.user.duka if not request.user.is_superuser else get_object_or_404(Duka, slug=slug)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            payment_method = data.get('payment_method', 'cash')
            
            if not items:
                return JsonResponse({'success': False, 'message': 'Hakuna bidhaa kwenye kapu.'}, status=400)
                
            total = 0
            sale = Sale.objects.create(
                duka=duka,
                cashier=request.user,
                total_amount=0,
                payment_method=payment_method
            )

            receipt_items = []
            for item in items:
                product = get_object_or_404(Product, id=item['id'], duka=duka)
                qty = int(item['quantity'])
                price = product.selling_price
                
                # Hakikisha stoo inatosha
                if product.stock_level < qty:
                    # Kama stoo haitoshi, uza kilichopo
                    qty = product.stock_level
                    
                if qty <= 0:
                    continue
                    
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=qty,
                    price_at_sale=price
                )
                total += qty * price
                
                # Punguza stock
                product.stock_level = max(0, product.stock_level - qty)
                product.save()
                
                receipt_items.append({
                    'name': product.name,
                    'qty': qty,
                    'price': float(price),
                    'subtotal': float(qty * price)
                })

            sale.total_amount = total
            sale.save()

            return JsonResponse({
                'success': True,
                'sale_id': sale.id,
                'total': float(total),
                'payment_method': sale.get_payment_method_display(),
                'date': sale.sale_date.strftime('%Y-%m-%d %H:%M:%S'),
                'items': receipt_items
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Njia isiyoruhusiwa'}, status=405)


@login_required
@store_access_required
def store_sales_report(request, slug):
    duka = request.user.duka if not request.user.is_superuser else get_object_or_404(Duka, slug=slug)
    sales = Sale.objects.filter(duka=duka).order_by('-sale_date')
    
    # Kokotoa faida na hasara
    # Kila sale item ina profit = quantity * (price_at_sale - product.cost_price)
    # Hii inaweza kufanyika kwenye python au DB queries.
    total_sales = sales.aggregate(sum=Sum('total_amount'))['sum'] or 0
    
    # Calculate profit from SaleItem
    sale_items = SaleItem.objects.filter(sale__duka=duka)
    total_profit = 0
    for item in sale_items:
        cost = item.product.cost_price
        total_profit += item.quantity * (item.price_at_sale - cost)

    context = {
        'duka': duka,
        'sales': sales,
        'total_sales': total_sales,
        'total_profit': total_profit,
    }
    return render(request, 'store/admin/sales_report.html', context)


@login_required
@store_access_required
def store_orders(request, slug):
    duka = request.user.duka if not request.user.is_superuser else get_object_or_404(Duka, slug=slug)
    orders = Order.objects.filter(duka=duka).order_by('-order_date')
    return render(request, 'store/admin/orders.html', {'duka': duka, 'orders': orders})


@login_required
@store_access_required
def store_order_update(request, slug, order_id):
    duka = request.user.duka if not request.user.is_superuser else get_object_or_404(Duka, slug=slug)
    order = get_object_or_404(Order, id=order_id, duka=duka)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in ['pending', 'completed', 'cancelled']:
            order.status = status
            order.save()
            messages.success(request, f"Hali ya agizo #{order.id} imebadilishwa kuwa '{order.get_status_display()}'")
            
    return redirect('store_orders_slug', slug=slug)
