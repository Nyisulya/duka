import os
import django

# Kuanzisha Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'duka_project.settings')
django.setup()

from core.models import Duka, CustomUser, Category, Product

def seed_data():
    print("Inaanza kuingiza data za majaribio...")
    
    # Kufuta data za zamani kama zipo (isipokuwa superusers)
    Duka.objects.all().delete()
    
    # 1. Unda Duka la 1 (Sabuni za Jumla)
    duka1 = Duka.objects.create(
        name="Mitindo Soap Wholesale",
        slug="mitindo",
        store_type="sabuni",
        logo="logos/mitindo_logo.png",
        theme_color="#10b981", # Green theme
        whatsapp_number="+255712345678",
        description="Wauzaji wa sabuni zote za kufulia, kuogea na sabuni za maji kwa bei ya jumla."
    )
    
    # Mmiliki wa duka la 1
    owner1 = CustomUser.objects.create_user(
        username="mitindo_owner",
        email="owner@mitindo.com",
        password="password123",
        first_name="Mitindo Owner",
        role="owner",
        duka=duka1
    )
    
    # Kategoria za Duka la 1
    cat1_1 = Category.objects.create(duka=duka1, name="Sabuni za Kufulia")
    cat1_2 = Category.objects.create(duka=duka1, name="Sabuni za Maji")
    
    # Bidhaa za Duka la 1
    Product.objects.create(
        duka=duka1,
        category=cat1_1,
        name="Sabuni ya Kipande (Mche wa 5)",
        description="Mche imara wa sabuni ya kufulia, unadumu kwa muda mrefu.",
        image="products/soap_bar.png",
        cost_price=8000.00,
        selling_price=10000.00,
        stock_level=50,
        min_stock_alert=5
    )
    
    Product.objects.create(
        duka=duka1,
        category=cat1_2,
        name="Sabuni ya Maji ya Ndimu (5 Litre)",
        description="Sabuni ya maji kwa ajili ya kuoshea vyombo na kusafishia sakafu yenye harufu nzuri ya ndimu.",
        image="products/liquid_soap.png",
        cost_price=12000.00,
        selling_price=15000.00,
        stock_level=20,
        min_stock_alert=5
    )
    
    Product.objects.create(
        duka=duka1,
        category=cat1_1,
        name="Sabuni ya Poda (Omo 1kg)",
        description="Sabuni ya unga ya kufulia nguo nyeupe na za rangi.",
        image="products/powder_soap.png",
        cost_price=4000.00,
        selling_price=5000.00,
        stock_level=3, # Critical Stock!
        min_stock_alert=5
    )
    
    # 2. Unda Duka la 2 (Mafuta ya Kupikia)
    duka2 = Duka.objects.create(
        name="Mafuta Bora Store",
        slug="mafuta",
        store_type="mafuta",
        logo="logos/mafuta_logo.png",
        theme_color="#f59e0b", # Amber/Yellow theme
        whatsapp_number="+255787654321",
        description="Mafuta safi ya alizeti na mawese moja kwa moja kutoka kiwandani."
    )
    
    # Mmiliki wa duka la 2
    owner2 = CustomUser.objects.create_user(
        username="mafuta_owner",
        email="owner@mafuta.com",
        password="password123",
        first_name="Mafuta Owner",
        role="owner",
        duka=duka2
    )
    
    # Kategoria za Duka la 2
    cat2_1 = Category.objects.create(duka=duka2, name="Mafuta ya Alizeti")
    cat2_2 = Category.objects.create(duka=duka2, name="Mafuta ya Nazi")
    
    # Bidhaa za Duka la 2
    Product.objects.create(
        duka=duka2,
        category=cat2_1,
        name="Mafuta ya Alizeti Kori (5 Litre)",
        description="Mafuta safi ya kupikia yasiyo na lehemu (cholesterol).",
        image="products/cooking_oil.png",
        cost_price=18000.00,
        selling_price=22000.00,
        stock_level=35,
        min_stock_alert=5
    )
    
    Product.objects.create(
        duka=duka2,
        category=cat2_2,
        name="Mafuta ya Nazi (1 Litre)",
        description="Mafuta safi ya nazi kwa ajili ya kupikia na matumizi ya ngozi.",
        image="products/coconut_oil.png",
        cost_price=6000.00,
        selling_price=7500.00,
        stock_level=40,
        min_stock_alert=5
    )
    
    print("Data za majaribio zimeingizwa kikamilifu!")
    print("\nUnaweza kutumia akaunti hizi za majaribio:")
    print("1. Duka la Sabuni: mitindo_owner (Nenosiri: password123)")
    print("2. Duka la Mafuta: mafuta_owner (Nenosiri: password123)")

if __name__ == "__main__":
    seed_data()
