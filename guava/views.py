from django.shortcuts import render, redirect
from . import models
from datetime import datetime
import calendar
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import login , logout, authenticate
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from django.forms import DateInput
from django.db.models import F,Q,Sum,Value
import math
from weasyprint import HTML
from django.template.loader import render_to_string
import tempfile
from django.urls import reverse
import qrcode
from io import BytesIO
from django.utils.timezone import now
from django.shortcuts import render
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import json


# Create your views here.
# Product to Commodity Conversion
product_to_commodity = {
    'Pastry': ('Crystal Guava', 0.33),
    'Blue Pea Tea': ('Blue Pea Flower', 0.1),
    'Dried Lemon': ('Lemon', 0.2),
    'Kale Chips': ('Kale', 0.25),
    'Crystal Guava Salad': ('Crystal Guava', 0.4)
}

# Month Translation (English → Indonesian)
month_translation = {
    'January': 'Januari',
    'February': 'Februari',
    'March': 'Maret',
    'April': 'April',
    'May': 'Mei',
    'June': 'Juni',
    'July': 'Juli',
    'August': 'Agustus',
    'September': 'September',
    'October': 'Oktober',
    'November': 'November',
    'December': 'Desember'
}

# Authentication Views
def login_view(request):
    if request.user.is_authenticated:
        group = None
        if request.user.groups.exists():
            group = request.user.groups.all()[0].name

        if group == 'inspection':
            return redirect('read_partner')
        elif group in ['admin', 'owner']:
            return redirect('base')
        else:
            return redirect('read_production')
    else:
        return render(request, "base/login.html")


def perform_login(request):
    if request.method != "POST":
        return HttpResponse("Method not Allowed")
    else:
        username_login = request.POST['username']
        password_login = request.POST['password']
        user_obj = authenticate(request, username=username_login, password=password_login)

        if user_obj is not None:
            login(request, user_obj)
            messages.success(request, "Login success")

            if user_obj.groups.filter(name='admin').exists() or user_obj.groups.filter(name='owner').exists():
                return redirect("base")
            elif user_obj.groups.filter(name='inspection').exists():
                return redirect("read_partner")
            elif user_obj.groups.filter(name='production').exists():
                return redirect('read_production')
            else:
                return redirect('login')
        else:
            messages.error(request, "Invalid username or password!")
            return redirect("login")


@login_required(login_url="login")
def logout_view(request):
    logout(request)
    messages.info(request, "Successfully logged out")
    return redirect('login')


@login_required(login_url="login")
def perform_logout(request):
    logout(request)
    return redirect("login")

@login_required(login_url="login")
@role_required(["owner", 'admin'])
def base(request):
    sale_details = models.SaleDetail.objects.all()
    local_harvest_details = models.LocalHarvestDetail.objects.all()
    partner_harvest_details = models.PartnerHarvestDetail.objects.all()
    commodities = models.Commodity.objects.all()
    commodity_dict = {i: 0 for i in commodities}

    for local in local_harvest_details:
        commodity = local.commodity_id
        commodity_dict[commodity] = commodity_dict.get(commodity, 0) + local.quantity

    for partner in partner_harvest_details:
        commodity = partner.commodity_id
        commodity_dict[commodity] = commodity_dict.get(commodity, 0) + partner.quantity

    list_commodities = list(commodity_dict.keys())
    list_quantities = list(commodity_dict.values())

    if request.method == 'GET':
        return render(request, 'base/dashboard.html', {
            'list_commodities': list_commodities,
            'list_quantities': list_quantities,
        })

    else:
        inp = request.POST['chart']
        list_markets = []
        list_quantities = []

        if inp == 'Product':
            for i in sale_details:
                if i.sale_id.market_id is not None and i.commodity_quantity:
                    list_markets.append(i.sale_id.market_id.market_name)
                    list_quantities.append(i.commodity_quantity)

        elif inp == 'Commodity':
            for i in sale_details:
                if i.sale_id.market_id is not None and i.product_quantity:
                    list_markets.append(i.sale_id.market_id.market_name)
                    list_quantities.append(i.product_quantity)

        market_dict = {}
        for a, b in zip(list_markets, list_quantities):
            market_dict[a] = market_dict.get(a, 0) + b

        final_markets = list(market_dict.keys())
        final_quantities = list(market_dict.values())

        return render(request, 'base/dashboard.html', {
            'list_commodities': list_commodities,
            'list_quantities': list_quantities,
            'list_markets': final_markets,
            'list_market_quantities': final_quantities,
        })


@login_required(login_url="login")
@role_required(["owner", 'admin','inspection'])
def read_partner(request):
    all_partners = models.Partner.objects.all().order_by('start_date')
    if not all_partners.exists():
        messages.error(request, "No Partner Data Found!")
    return render(request, 'partner/read_partner.html', {
        'all_partners': all_partners
    })


@login_required(login_url="login")
@role_required(["owner", 'admin'])
def create_partner(request):
    if request.method == "GET":
        return render(request, 'partner/create_partner.html')
    else:
        partner_name = request.POST["partner_name"].lower()
        partner_obj = models.Partner.objects.filter(partner_name=partner_name)

        if partner_obj.exists():
            messages.error(request, "Partner name already exists")
            return redirect("create_partner")

        land_area = int(request.POST["land_area"])
        if land_area < 100:
            messages.error(request, "Land area must be greater than 100 m²")
            return redirect("create_partner")

        min_quantity = request.POST['min_quantity']
        status = request.POST["partner_status"].lower() == "active"

        data = models.Partner(
            partner_name=partner_name,
            partner_address=request.POST["partner_address"],
            partner_phone=request.POST["partner_phone"],
            start_date=request.POST["start_date"],
            contract_duration=request.POST["contract_duration"],
            email = request.POST["email"],
            land_area=land_area,
            min_quantity=min_quantity,
            partner_status=status
        )
        data.save()

        models.ActivityLog.objects.create(
            user=request.user,
            action="Add Partner",
            description=f"Added new partner: {data.partner_name}, land {data.land_area} m², contract {data.contract_duration} months."
        )

        messages.success(request, "Partner successfully added!")
        return redirect("read_partner")


@login_required(login_url="login")
@role_required(["owner", 'admin'])
def update_partner(request, id):
    try:
        partner_obj = models.Partner.objects.get(partner_id=id)
    except models.Partner.DoesNotExist:
        messages.error(request, "Partner not found!")
        return redirect('read_partner')

    start_date = partner_obj.start_date.strftime('%Y-%m-%d')
    partner_status = 'Active' if partner_obj.partner_status else 'Inactive'

    if request.method == "GET":
        return render(request, 'partner/update_partner.html', {
            'partner_obj': partner_obj,
            'partner_status': partner_status,
            'start_date': start_date
        })
    else:
        partner_name = request.POST["partner_name"].lower()
        if models.Partner.objects.filter(partner_name=partner_name).exclude(partner_id=id).exists():
            messages.error(request, "Partner name already exists!")
            return render(request, 'partner/update_partner.html', {
                'partner_obj': partner_obj,
                'partner_status': partner_status,
                'start_date': start_date
            })

        land_area = int(request.POST["land_area"])
        if land_area < 100:
            messages.error(request, "Land area must be greater than 100 m²")
            return render(request, 'partner/update_partner.html', {
                'partner_obj': partner_obj,
                'partner_status': partner_status,
                'start_date': start_date
            })

        old_status = partner_obj.partner_status

        partner_obj.partner_name = partner_name
        partner_obj.partner_address = request.POST["partner_address"]
        partner_obj.partner_phone = request.POST["partner_phone"]
        partner_obj.start_date = request.POST["start_date"]
        partner_obj.contract_duration = request.POST["contract_duration"]
        partner_obj.land_area = land_area
        partner_obj.partner_status = request.POST["partner_status"].lower() == "active"
        partner_obj.save()

        models.ActivityLog.objects.create(
            user=request.user,
            action="Update Partner",
            description=(
                f"Updated partner: {partner_obj.partner_name},\n"
                f"Address: {partner_obj.partner_address},\n"
                f"Status: {old_status} → {'Active' if partner_obj.partner_status else 'Inactive'}.\n"
            )
        )

        messages.success(request, "Partner successfully updated!")
        return redirect('read_partner')


@login_required(login_url="login")
@role_required(["owner"])
def delete_partner(request, id):
    partner_obj = models.Partner.objects.get(partner_id=id)
    name = partner_obj.partner_name
    address = partner_obj.partner_address
    phone = partner_obj.partner_phone

    models.ActivityLog.objects.create(
        user=request.user,
        action="Delete Partner",
        description=f"Deleted partner: {name}, Address: {address}, Phone: {phone}."
    )

    partner_obj.delete()
    messages.success(request, "Partner successfully deleted!")
    return redirect('read_partner')


'''CRUD PENJUALAN'''
@login_required(login_url='login')
@role_required(['owner', 'admin'])
def create_sale(request):
    market_obj = models.Market.objects.all()
    product_obj = models.Product.objects.all()
    commodity_obj = models.Commodity.objects.all()

    qr_data = {
        'qr_commodity': request.GET.get('qr_commodity', ''), 
        'qr_expiry': request.GET.get('qr_expiry', ''),
        'qr_quantity': request.GET.get('qr_quantity', ''),
    }

    if request.method == 'GET':
        return render(request, 'sales/create_sales.html', {
            'market_obj': market_obj,
            'product_obj': product_obj,
            'commodity_obj': commodity_obj,
            'qr_data': qr_data,
        })

    else:
        market = request.POST.get('market_id')
        date = request.POST.get('date')

        product_qty = request.POST.getlist('product_qty')
        commodity_qty = request.POST.getlist('commodity_qty')
        products = request.POST.getlist('product')
        commodities = request.POST.getlist('commodity')

        qr_commodities = request.POST.getlist('qr_commodity') 
        qr_expiry = request.POST.getlist('qr_expiry')
        qr_quantities = request.POST.getlist('qr_quantity')

        sale = models.Sale(
            market_id=models.Market.objects.get(market_id=market),
            date=date,
        )
        sale.save()
        sale_detail_ids = []

        # Sales from manual form
        for p, c, qp, qc in zip(products, commodities, product_qty, commodity_qty):
            if c and p and qp and qc:
                detail = models.SaleDetail(
                    sale_id=sale,
                    product_id=models.Product.objects.get(product_id=p),
                    commodity_id=models.Commodity.objects.get(commodity_id=c),
                    product_quantity=qp,
                    commodity_quantity=qc,
                )
            elif c and not p and not qp and qc:
                detail = models.SaleDetail(
                    sale_id=sale,
                    product_id=None,
                    commodity_id=models.Commodity.objects.get(commodity_id=c),
                    product_quantity=None,
                    commodity_quantity=qc,
                )
            elif not c and p and qp and not qc:
                detail = models.SaleDetail(
                    sale_id=sale,
                    product_id=models.Product.objects.get(product_id=p),
                    commodity_id=None,
                    product_quantity=qp,
                    commodity_quantity=None,
                )
            else:
                continue
            detail.save()
            sale_detail_ids.append(detail.sale_detail_id)

        # Sales from QR
        for commodity, expiry, quantity in zip(qr_commodities, qr_expiry, qr_quantities):
            if not commodity or not quantity:
                continue

            try:
                commodity_obj = models.Commodity.objects.get(commodity_id=commodity)

                detail = models.SaleDetail(
                    sale_id=sale,
                    product_id=None,
                    commodity_id=commodity_obj,
                    product_quantity=None,
                    commodity_quantity=quantity,
                )
                detail.save()
                sale_detail_ids.append(detail.sale_detail_id)

            except models.Commodity.DoesNotExist:
                messages.error(request, f"Commodity with ID {commodity} not found.")
                sale.delete()
                return redirect('create_sale')

        if not sale_detail_ids:
            messages.error(request, 'No valid sale data was saved.')
            sale.delete()
            return redirect('create_sale')

        market_name = models.Market.objects.get(market_id=market).market_name
        
        models.ActivityLog.objects.create(
            user=request.user,
            action="Add Sale",
            description=f"Added a new sale at {market_name} on {date}"
        )

        messages.success(request, 'Sale data has been successfully added!')
        return redirect('read_sale')


@login_required(login_url='login')
@role_required(['owner', 'admin'])
def read_sale(request):
    sale_obj = models.Sale.objects.all()
    sale_detail_obj = models.SaleDetail.objects.all()
    if not sale_obj.exists():
        messages.error(request, "No sales data found!")
    return render(request,
                  'sales/read_sales.html',
                  {
                      'sale_obj': sale_obj,
                      'sale_detail_obj': sale_detail_obj,
                  })


@login_required(login_url='login')
@role_required(['owner', 'admin'])
def update_sale(request, id):
    market_obj = models.Market.objects.all()
    product_obj = models.Product.objects.all()
    commodity_obj = models.Commodity.objects.all()

    sale = models.Sale.objects.get(sale_id=id)
    sale_date = datetime.strftime(sale.date, '%Y-%m-%d')
    market_name = sale.market_id.market_name

    if request.method == 'GET':
        return render(request, 'sales/update_sales.html', {
            'sale_date': sale_date,
            'market_name': market_name,
            'sale': sale,
            'market_obj': market_obj,
            'product_obj': product_obj,
            'commodity_obj': commodity_obj,
            'id': id,
        })
    
    else:
        market = request.POST['market_id']
        date = request.POST['date']

        old_market = sale.market_id.market_name
        old_date = sale.date

        sale.sale_id = sale.sale_id
        sale.market_id = models.Market.objects.get(market_id=market)
        sale.date = date

        sale.save()
        
        models.ActivityLog.objects.create(
            user=request.user,
            action="Update Sale",
            description=f"Updated sale ID: {sale.sale_id}. "
                        f"Old Market: {old_market},\n"
                        f"Old Sale Date: {old_date}\n"
        )
        
        messages.success(request, "Sale data has been successfully updated!")
        return redirect('read_sale')


@login_required(login_url='login')
@role_required(['owner'])
def delete_sale(request, id):
    sale = models.Sale.objects.get(sale_id=id)
    
    market_name = sale.market_id.market_name
    date = sale.date
    
    models.ActivityLog.objects.create(
        user=request.user,
        action="Delete Sale",
        description=f"Deleted sale with ID: {id} at market {market_name} on {date}"
    )
    
    sale.delete()
    messages.error(request, "Sale data has been deleted!")
    return redirect('read_sale')



'''CUD DETAIL PENJUALAN'''
@login_required(login_url='login')
@role_required(['owner', 'admin'])
def create_sale_detail(request, id):
    commodity_obj = models.Commodity.objects.all()
    product_obj = models.Product.objects.all()

    if request.method == 'GET':
        return render(request, 'sales/create_detail_sales.html', {
            'commodity_obj': commodity_obj,
            'product_obj': product_obj,
        })

    else:
        product_qty = request.POST.getlist('product_qty')
        commodity_qty = request.POST.getlist('commodity_qty')
        products = request.POST.getlist('product')
        commodities = request.POST.getlist('commodity')

        detail_ids = []

        for product, commodity, pq, cq in zip(products, commodities, product_qty, commodity_qty):
            if commodity and product and pq and cq:
                detail = models.SaleDetail(
                    sale_id=models.Sale.objects.get(sale_id=id),
                    product_id=models.Product.objects.get(product_id=product),
                    commodity_id=models.Commodity.objects.get(commodity_id=commodity),
                    product_quantity=pq,
                    commodity_quantity=cq,
                )
                detail.save()
                detail_ids.append(detail.sale_detail_id)
                print("condition 1")

            elif commodity and not product and not pq and cq:
                detail = models.SaleDetail(
                    sale_id=models.Sale.objects.get(sale_id=id),
                    product_id=None,
                    commodity_id=models.Commodity.objects.get(commodity_id=commodity),
                    product_quantity=None,
                    commodity_quantity=cq,
                )
                detail.save()
                detail_ids.append(detail.sale_detail_id)
                print("condition 2")

            elif not commodity and product and pq and not cq:
                detail = models.SaleDetail(
                    sale_id=models.Sale.objects.get(sale_id=id),
                    product_id=models.Product.objects.get(product_id=product),
                    commodity_id=None,
                    product_quantity=pq,
                    commodity_quantity=None,
                )
                detail.save()
                detail_ids.append(detail.sale_detail_id)
                print("condition 3")

            else:
                get_details = models.SaleDetail.objects.filter(sale_detail_id__in=detail_ids)
                get_details.delete()
                print("condition 4")
                messages.error(request, "Sale detail must have at least one valid product/commodity with its quantity. Please try again!")
                return redirect(reverse('create_detail_sales', args=[id]))

        messages.success(request, "Sale detail has been successfully added!")
        return redirect('read_sale')


@login_required(login_url='login')
@role_required(['owner', 'admin'])
def update_sale_detail(request, id):
    commodity = models.Commodity.objects.all()
    product = models.Product.objects.all()
    getsales = models.Sale.objects.all()
    detail = models.SaleDetail.objects.get(sale_detail_id=id)
    sale_id = detail.sale_id.sale_id

    # Render form for GET request
    if detail.product_id is None:
        commodity_id = detail.commodity_id.commodity_id
        commodity_qty = detail.commodity_quantity
        if request.method == 'GET':
            return render(request, 'sales/update_sale_detail.html', {
                'commodity_qty': commodity_qty,
                'commodity_id': commodity_id,
                'commodity': commodity,
                'product': product,
                'sale_id': sale_id,
                'detail': detail,
                'getsales': getsales,
                'id': id,
            })

    if detail.commodity_id is None:
        product_id = detail.product_id.product_id
        product_qty = detail.product_quantity
        if request.method == 'GET':
            return render(request, 'sales/update_sale_detail.html', {
                'product_qty': product_qty,
                'product_id': product_id,
                'commodity': commodity,
                'product': product,
                'sale_id': sale_id,
                'detail': detail,
                'getsales': getsales,
                'id': id,
            })

    else:
        commodity_id = detail.commodity_id.commodity_id
        commodity_qty = detail.commodity_quantity
        product_id = detail.product_id.product_id
        product_qty = detail.product_quantity
        if request.method == 'GET':
            return render(request, 'sales/update_sale_detail.html', {
                'commodity_id': commodity_id,
                'commodity_qty': commodity_qty,
                'product_qty': product_qty,
                'product_id': product_id,
                'commodity': commodity,
                'product': product,
                'sale_id': sale_id,
                'detail': detail,
                'getsales': getsales,
                'id': id,
            })

    # Handle POST request
    sale_id_post = request.POST['sale_id']
    product_qty = request.POST['product_qty']
    commodity_qty = request.POST['commodity_qty']
    product = request.POST['product']
    commodity = request.POST['commodity']

    if commodity and product and product_qty and commodity_qty:
        detail.sale_id = models.Sale.objects.get(sale_id=sale_id_post)
        detail.product_id = models.Product.objects.get(product_id=product)
        detail.commodity_id = models.Commodity.objects.get(commodity_id=commodity)
        detail.product_quantity = product_qty
        detail.commodity_quantity = commodity_qty
        detail.save()
        print("condition 1")

    elif commodity and not product and not product_qty and commodity_qty:
        detail.sale_id = models.Sale.objects.get(sale_id=sale_id_post)
        detail.product_id = None
        detail.commodity_id = models.Commodity.objects.get(commodity_id=commodity)
        detail.product_quantity = None
        detail.commodity_quantity = commodity_qty
        detail.save()
        print("condition 2")

    elif not commodity and product and product_qty and not commodity_qty:
        detail.sale_id = models.Sale.objects.get(sale_id=sale_id_post)
        detail.product_id = models.Product.objects.get(product_id=product)
        detail.commodity_id = None
        detail.product_quantity = product_qty
        detail.commodity_quantity = None
        detail.save()
        print("condition 3")

    else:
        print("invalid condition")
        messages.error(request, "Sale detail must have at least one valid product/commodity with its quantity. Please try again!")
        return redirect(reverse('update_sale_detail', args=[id]))

    messages.success(request, "Sale detail has been successfully updated!")
    return redirect('read_sale')


@login_required(login_url='login')
@role_required(['owner'])
def delete_sale_detail(request, id):
    detail = models.SaleDetail.objects.get(sale_detail_id=id)
    detail.delete()
    messages.error(request, "Sale detail has been deleted!")
    return redirect('read_sale')

""" CRUD PRODUCT """
@login_required(login_url='login')
@role_required(['owner'])
def create_product(request):
    if request.method == 'GET':
        return render(request, 'product/create_product.html')
    
    else:
        product_name = request.POST['product_name']
        product_unit = request.POST['product_unit']
        product_price = request.POST['product_price']

        product_obj = models.Product.objects.filter(product_name=product_name)
        if product_obj.exists():
            messages.error(request, "Product name already exists!")
            return redirect('create_product')

        data = models.Product(
            product_name=product_name,
            product_unit=product_unit,
            product_price=product_price,
        )
        data.save()
        
        models.ActivityLog(
            user=request.user,
            action="Add Product",
            description=(
                f"Added new product: {data.product_name}, "
                f"unit '{data.product_unit}', price {data.product_price}."
            )
        ).save()

        messages.success(request, "Product has been successfully added!")
        return redirect('read_product')


@login_required(login_url='login')
@role_required(['owner', 'admin', 'production'])
def read_product(request):
    product_obj = models.Product.objects.all()
    if not product_obj.exists():
        messages.error(request, "No product data found!")

    return render(request, 'product/read_product.html', {
        'product_obj': product_obj
    })


@login_required(login_url='login')
@role_required(['owner'])
def update_product(request, id):
    product = models.Product.objects.get(product_id=id)

    if request.method == 'GET':
        return render(request, 'product/update_product.html', {
            'product': product,
            'id': id
        })
    
    else:
        product_name = request.POST['product_name']
        product_unit = request.POST['product_unit']
        product_price = request.POST['product_price']

        product_obj = models.Product.objects.filter(product_name=product_name)
        if product_obj.exists() and product.product_name != product_name:
            messages.error(request, "Product already exists!")
            return redirect('update_product', id)

        old_name = product.product_name
        old_unit = product.product_unit
        old_price = product.product_price

        product.product_name = product_name
        product.product_unit = product_unit
        product.product_price = product_price
        product.save()
        
        models.ActivityLog(
            user=request.user,
            action="Update Product",
            description=(
                f"Updated product ID {id}:\n "
                f"Name '{old_name}' → '{product_name}',\n "
                f"Unit '{old_unit}' → '{product_unit}',\n "
                f"Price {old_price} → {product_price}.\n"
            )
        ).save()

        messages.success(request, "Product has been successfully updated!")
        return redirect('read_product')


@login_required(login_url='login')
@role_required(['owner'])
def delete_product(request, id):
    product = models.Product.objects.get(product_id=id)
    name = product.product_name
    price = product.product_price

    product.delete()

    models.ActivityLog(
        user=request.user,
        action="Delete Product",
        description=(
            f"Deleted product: {name}, price {price}."
        )
    ).save()

    messages.error(request, "Product has been deleted!")
    return redirect('read_product')


""" CRUD COMMODITY """
@login_required(login_url='login')
@role_required(['owner'])
def create_commodity(request):
    grade_obj = models.Grade.objects.all()
    
    if request.method == 'GET':
        return render(request, 'commodity/create_commodity.html', {
            'grade_obj': grade_obj
        })
    
    else:
        grade_name = request.POST['grade_name']
        commodity_name = request.POST['commodity_name']
        purchase_price = request.POST['purchase_price']
        selling_price = request.POST['selling_price']

        commodity_obj = models.Commodity.objects.filter(
            commodity_name=commodity_name,
            grade_id__grade_name=grade_name
        )

        if commodity_obj.exists():
            messages.error(request, "Commodity already exists!")
        
        else:
            grade_instance = models.Grade.objects.get(grade_name=grade_name)
            data = models.Commodity(
                grade_id=grade_instance,
                commodity_name=commodity_name,
                purchase_price=purchase_price,
                selling_price=selling_price,
            )
            data.save()

            models.ActivityLog(
                user=request.user,
                action="Add Commodity",
                description=(
                    f"Added new commodity: {data.commodity_name}, "
                    f"Grade {data.grade_id.grade_name}, "
                    f"Purchase {data.purchase_price}, "
                    f"Selling {data.selling_price}."
                )
            ).save()

            messages.success(request, "Commodity has been successfully added!")

        return redirect('read_commodity')


@login_required(login_url='login')
@role_required(['owner', 'admin', 'inspection'])
def read_commodity(request):
    commodity_obj = models.Commodity.objects.all()
    if not commodity_obj.exists():
        messages.error(request, "No commodity data found!")

    return render(request, 'commodity/read_commodity.html', {
        'commodity_obj': commodity_obj
    })


@login_required(login_url='login')
@role_required(['owner'])
def update_commodity(request, id):
    grade_obj = models.Grade.objects.all()
    commodity = models.Commodity.objects.get(commodity_id=id)
    grade_name = commodity.grade_id.grade_name

    if request.method == 'GET':
        return render(request, 'commodity/update_commodity.html', {
            'commodity': commodity,
            'grade_name': grade_name,
            'grade_obj': grade_obj,
            'id': id,
        })

    else:
        new_grade_name = request.POST['grade_name']
        new_commodity_name = request.POST['commodity_name']
        new_purchase_price = request.POST['purchase_price']
        new_selling_price = request.POST['selling_price']

        commodity_obj = models.Commodity.objects.filter(
            commodity_name=new_commodity_name,
            grade_id__grade_name=new_grade_name
        )
        if commodity_obj.exists() and (
            commodity.commodity_name != new_commodity_name 
            or commodity.grade_id.grade_name != new_grade_name
        ):
            messages.error(request, "Commodity already exists!")
            return redirect('update_commodity', id)

        old_name = commodity.commodity_name
        old_grade = commodity.grade_id.grade_name
        old_purchase_price = commodity.purchase_price
        old_selling_price = commodity.selling_price

        commodity.grade_id = models.Grade.objects.get(grade_name=new_grade_name)
        commodity.commodity_name = new_commodity_name
        commodity.purchase_price = new_purchase_price
        commodity.selling_price = new_selling_price
        commodity.save()

        models.ActivityLog(
            user=request.user,
            action="Update Commodity",
            description=(
                f"Updated commodity ID {commodity.commodity_id}:\n "
                f"From: {old_name} (Grade: {old_grade}, Purchase: {old_purchase_price}, Selling: {old_selling_price})\n "
                f"To: {new_commodity_name} (Grade: {new_grade_name}, Purchase: {new_purchase_price}, Selling: {new_selling_price})\n"
            )
        ).save()

        messages.success(request, "Commodity has been successfully updated!")
        return redirect('read_commodity')


@login_required(login_url='login')
@role_required(['owner'])
def delete_commodity(request, id):
    commodity = models.Commodity.objects.get(commodity_id=id)
    name = commodity.commodity_name
    grade = commodity.grade_id.grade_name

    models.ActivityLog(
        user=request.user,
        action="Delete Commodity",
        description=(
            f"Deleted commodity: {name} (Grade: {grade})."
        )
    ).save()
    
    commodity.delete()
    messages.error(request, "Commodity has been deleted!")
    return redirect('read_commodity')

""" CRUD GRADE """
@login_required(login_url='login')
@role_required(['owner', 'admin', 'inspection'])
def read_grade(request):
    gradeobj = models.Grade.objects.all()
    return render(request, 'grade/read_grade.html', {'gradeobj': gradeobj})

@login_required(login_url='login')
@role_required(['owner'])
def create_grade(request):
    if request.method == "GET":
        return render(request, 'grade/create_grade.html')
    else:
        grade_name = request.POST["grade_name"]
        grade_obj = models.Grade.objects.filter(grade_name=grade_name)

        if grade_obj.exists():
            messages.error(request, "Grade name already exists!")
            return redirect("create_grade")
        else:
            description = request.POST["grade_description"]

            data = models.Grade(
                grade_name=grade_name,
                grade_description=description,
            )
            data.save()
            messages.success(request, "Grade successfully added!")

            models.ActivityLog(
                user=request.user,
                action="Add Grade",
                description=f"Added new grade: {data.grade_name} - {data.grade_description}."
            ).save()

        return redirect("read_grade")

@login_required(login_url='login')
@role_required(['owner'])
def update_grade(request, id):
    try:
        grade_obj = models.Grade.objects.get(grade_id=id)
    except models.Grade.DoesNotExist:
        messages.error(request, "Grade not found!")
        return redirect('read_grade')

    if request.method == "GET":
        return render(request, 'grade/update_grade.html', {
            'gradeobj': grade_obj,
        })
    else:
        grade_name = request.POST["grade_name"]
        if models.Grade.objects.filter(grade_name=grade_name).exclude(grade_id=id).exists():
            messages.error(request, "Grade name already exists!")
            return render(request, 'grade/update_grade.html', {
                'gradeobj': grade_obj,
            })

        old_name = grade_obj.grade_name
        old_desc = grade_obj.grade_description

        grade_obj.grade_name = request.POST["grade_name"]
        grade_obj.grade_description = request.POST["grade_description"]
        grade_obj.save()

        models.ActivityLog(
            user=request.user,
            action="Update Grade",
            description=f"Updated grade from '{old_name} - {old_desc}' \n to '{grade_obj.grade_name} - {grade_obj.grade_description}'."
        ).save()

        messages.success(request, "Grade successfully updated!")
        return redirect('read_grade')

@login_required(login_url='login')
@role_required(['owner'])
def delete_grade(request, id):
    grade_obj = models.Grade.objects.get(grade_id=id)
    grade_name = grade_obj.grade_name
    grade_description = grade_obj.grade_description

    grade_obj.delete()

    models.ActivityLog(
        user=request.user,
        action="Delete Grade",
        description=f"Deleted grade: {grade_name} - {grade_description}."
    ).save()

    messages.success(request, "Grade successfully deleted!")
    return redirect('read_grade')


""" CRUD MARKET (PASAR) """
@login_required(login_url='login')
@role_required(['owner'])
def create_market(request):
    if request.method == 'GET':
        return render(request, 'market/create_market.html')
    else:
        market_name = request.POST['market_name']
        market_address = request.POST['market_address']

        market_obj = models.Market.objects.filter(market_name=market_name)
        if market_obj.exists():
            messages.error(request, 'Market name already exists!')
        else:
            data = models.Market(
                market_name=market_name,
                market_address=market_address,
            )
            data.save()

            models.ActivityLog(
                user=request.user,
                action="Add Market",
                description=f"Added new market: {data.market_name}, located at {data.market_address}."
            ).save()
            messages.success(request, 'Market successfully added!')

        return redirect('read_market')

@login_required(login_url='login')
@role_required(['owner', 'admin'])
def read_market(request):
    market_obj = models.Market.objects.all()
    if not market_obj.exists():
        messages.error(request, "No market data found!")

    return render(request, 'market/read_market.html', {
        'market_obj': market_obj
    })

@login_required(login_url='login')
@role_required(['owner'])
def update_market(request, id):
    market_obj = models.Market.objects.get(market_id=id)
    if request.method == 'GET':
        return render(request, 'market/update_market.html', {
            'getmarket': market_obj,
            'id': id
        })
    else:
        market_name = request.POST['market_name']
        market_address = request.POST['market_address']

        existing = models.Market.objects.filter(market_name=market_name)
        if existing.exists() and market_obj.market_name != market_name:
            messages.error(request, 'Market name already exists!')
            return redirect('update_market', id)

        old_name = market_obj.market_name
        old_address = market_obj.market_address

        market_obj.market_name = market_name
        market_obj.market_address = market_address
        market_obj.save()

        models.ActivityLog(
            user=request.user,
            action="Update Market",
            description=f"Updated market from '{old_name} - {old_address}' \n to '{market_name} - {market_address}'."
        ).save()

        messages.success(request, 'Market successfully updated!')
        return redirect('read_market')

@login_required(login_url='login')
@role_required(['owner'])
def delete_market(request, id):
    market_obj = models.Market.objects.get(market_id=id)
    name = market_obj.market_name
    address = market_obj.market_address

    market_obj.delete()

    models.ActivityLog(
        user=request.user,
        action="Delete Market",
        description=f"Deleted market {name} located at {address}."
    ).save()

    messages.success(request, "Market successfully deleted!")
    return redirect('read_market')

from datetime import datetime

@login_required(login_url='login')
@role_required(['owner'])
def sales_report(request):
    start = request.GET.get('start')
    end = request.GET.get('end')

    if start and end:
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")

        sales_qs = models.Sale.objects.filter(date__range=(start, end)).order_by('date')
        if not sales_qs.exists():
            messages.error(request, "No sales data found!")
            return redirect('sales_report')

        detail_sales_list = []
        total_sales_list = []

        for sale in sales_qs:
            detail_list = []
            item_prices = []

            sale_details = models.SaleDetail.objects.filter(sale_id=sale.sale_id)
            if not sale_details.exists():
                continue

            for d in sale_details:
                # safer calculation
                commodity_price = (d.commodity_id.selling_price * d.commodity_quantity) if d.commodity_id else 0
                product_price = (d.product_id.product_price * d.product_quantity) if d.product_id else 0
                item_prices.append(commodity_price + product_price)

            total_price = sum(item_prices)
            detail_list.extend([sale, sale_details, item_prices, total_price])

            total_sales_list.append(total_price)
            detail_sales_list.append(detail_list)

        grand_total = sum(total_sales_list)

        return render(request, 'report/sales_report.html', {
            'detail_sales_list': detail_sales_list,
            'grand_total': grand_total,
            'start': start_date,
            'end': end_date,
        })

    else:
        # no filter, show all
        sales_qs = models.Sale.objects.all().order_by('date')
        detail_sales_list = []
        total_sales_list = []

        for sale in sales_qs:
            detail_list = []
            item_prices = []

            sale_details = models.SaleDetail.objects.filter(sale_id=sale.sale_id)
            if not sale_details.exists():
                continue

            for d in sale_details:
                komoditas_price = (d.commodity_id.selling_price * d.commodity_quantity) if d.commodity_id else 0
                product_price = (d.product_id.product_price * d.product_quantity) if d.product_id else 0
                item_prices.append(komoditas_price + product_price)

            total_price = sum(item_prices)
            detail_list.extend([sale, sale_details, item_prices, total_price])

            total_sales_list.append(total_price)
            detail_sales_list.append(detail_list)

        grand_total = sum(total_sales_list)

        return render(request, 'report/sales_report.html', {
            'detail_sales_list': detail_sales_list,
            'grand_total': grand_total,
        })


""" PARTNER HARVEST (PANEN MITRA) """
@login_required(login_url="login")
@role_required(["owner", "admin", "inspection"])
def read_partner_harvest(request):
    harvest_qs = models.PartnerHarvestDetail.objects.all().order_by('partner_harvest_id__harvest_date')

    if not harvest_qs.exists():
        messages.error(request, 'No partner harvest data found!')
        return render(request, 'harvest/partner/read_partner_harvest.html')

    return render(request, 'harvest/partner/read_partner_harvest.html', {
        'harvest_qs': harvest_qs,
    })

            
@login_required(login_url="login")
@role_required(["owner"])
def create_partner_harvest(request):
    all_commodities = models.Commodity.objects.all()
    all_partners = models.Partner.objects.all()

    if request.method == "GET":
        return render(request, 'harvest/partner/create_partner_harvest.html', {
            'all_commodities': all_commodities,
            'all_partners': all_partners,
        })

    else:
        harvest_date = request.POST["harvest_date"]
        partner_id = request.POST["partner_name"]
        commodity_list = request.POST.getlist("commodity")
        batch_list = request.POST.getlist("batch")
        expiry_list = request.POST.getlist("expiry_date")
        quantity_list = request.POST.getlist("quantity")

        partner_harvest = models.PartnerHarvest(
            harvest_date=harvest_date,
            partner_id=models.Partner.objects.get(partner_id=partner_id)
        )
        partner_harvest.save()

        for commodity_id, batch, expiry_date, quantity in zip(
            commodity_list, batch_list, expiry_list, quantity_list
        ):
            commodity_obj = models.Commodity.objects.get(commodity_id=commodity_id)

            if not qr_already_generated(commodity_id, expiry_date):
                models.PartnerHarvestDetail(
                    partner_harvest_id=partner_harvest,
                    commodity_id=commodity_obj,
                    batch=batch,
                    expiry_date=expiry_date,
                    quantity=quantity,
                ).save()

                qr_data = generate_qr_data(
                    str(commodity_obj),
                    expiry_date,
                    quantity
                )
                qr_image = generate_qr_image(qr_data)

                response = HttpResponse(qr_image.getvalue(), content_type="image/png")
                response['Content-Disposition'] = (
                    f'attachment; filename="qr_{commodity_obj.commodity_name}_'
                    f'{commodity_obj.grade_id.grade_name}_{expiry_date}.png"'
                )
                return response
            else:
                models.PartnerHarvestDetail(
                    partner_harvest_id=partner_harvest,
                    commodity_id=commodity_obj,
                    batch=batch,
                    expiry_date=expiry_date,
                    quantity=quantity,
                ).save()

                models.ActivityLog(
                    user=request.user,
                    action="Add Partner Harvest",
                    description=(
                        f"Add partner harvest from {partner_harvest.partner_id.partner_name}, "
                        f"harvest date {partner_harvest.harvest_date}"
                    )
                ).save()

                messages.warning(
                    request,
                    f"QR not created because data {commodity_id} with expiry {expiry_date} already exists."
                )

    messages.success(request, "Partner harvest successfully added!")
    return redirect("total_commodities")


@login_required(login_url="login")
@role_required(["owner", "admin", "inspection"])
def update_partner_harvest(request, id):
    try:
        detail_obj = models.PartnerHarvestDetail.objects.get(partner_harvest_detail_id=id)
    except models.PartnerHarvestDetail.DoesNotExist:
        messages.error(request, "Partner harvest data not found!")
        return redirect('read_partner_harvest')

    partners = models.Partner.objects.filter(partner_status=True)
    commodities = models.Commodity.objects.all()

    if request.method == "GET":
        harvest_date = detail_obj.partner_harvest_id.harvest_date.strftime('%Y-%m-%d')
        expiry_date = detail_obj.expiry_date.strftime('%Y-%m-%d')
        return render(request, 'harvest/partner/update_partner_harvest.html', {
            'detail_obj': detail_obj,
            'partners': partners,
            'commodities': commodities,
            'harvest_date': harvest_date,
            'expiry_date': expiry_date,
        })

    else:
        partner = models.Partner.objects.get(partner_id=request.POST["partner"])
        commodity = models.Commodity.objects.get(commodity_id=request.POST["commodity"])

        detail_obj.partner_harvest_id.partner_id = partner
        detail_obj.partner_harvest_id.harvest_date = request.POST["harvest_date"]
        detail_obj.commodity_id = commodity
        detail_obj.batch = request.POST["batch"]
        detail_obj.expiry_date = request.POST["expiry_date"]
        detail_obj.quantity = request.POST["quantity"]

        detail_obj.partner_harvest_id.save()
        detail_obj.save()

        models.ActivityLog(
            user=request.user,
            action="Update Partner Harvest",
            description=(
                f"Update partner harvest for {partner.partner_name}, "
                f"harvest date {detail_obj.partner_harvest_id.harvest_date}"
            )
        ).save()

        messages.success(request, "Partner harvest updated successfully!")
        return redirect('read_partner_harvest')


@login_required(login_url="login")
@role_required(["owner"])
def delete_partner_harvest(request, id):
    try:
        detail_obj = models.PartnerHarvestDetail.objects.get(partner_harvest_detail_id=id)
    except models.PartnerHarvestDetail.DoesNotExist:
        messages.error(request, "Partner harvest data not found!")
        return redirect('read_partner_harvest')

    partner_name = detail_obj.partner_harvest_id.partner_id.partner_name
    harvest_date = detail_obj.partner_harvest_id.harvest_date.strftime('%Y-%m-%d')

    models.ActivityLog(
        user=request.user,
        action="Delete Partner Harvest",
        description=f"Deleted partner harvest: {partner_name}, harvest date {harvest_date}"
    ).save()

    detail_obj.delete()
    messages.success(request, "Partner harvest deleted successfully!")
    return redirect('read_partner_harvest')


'''PANEN LOKAL'''
@login_required(login_url="login")
@role_required(["owner", "admin", "inspection"])
def read_local_harvest(request):
    harvests = models.LocalHarvestDetail.objects.all().order_by('local_harvest_id__harvest_date')
    if not harvests.exists():
        messages.error(request, "No Local Harvest data found!")
        return render(request, 'harvest/local/read_local_harvest.html')
    return render(request, 'harvest/local/read_local_harvest.html', {
        'harvests': harvests,
    })


@login_required(login_url="login")
@role_required(["owner"])
def create_local_harvest(request):
    all_commodities = models.Commodity.objects.all()

    if request.method == "GET":
        return render(request, 'harvest/local/create_local_harvest.html', {
            'all_commodities': all_commodities,
        })
    else:
        harvest_date = request.POST["harvest_date"]
        commodity_list = request.POST.getlist("commodity")
        batch_list = request.POST.getlist("batch")
        expiry_list = request.POST.getlist("expiry_date")
        quantity_list = request.POST.getlist("quantity")

        local_harvest = models.LocalHarvest(
            harvest_date=harvest_date
        )
        local_harvest.save()

        for commodity_id, batch, expiry_date, quantity in zip(
            commodity_list, batch_list, expiry_list, quantity_list
        ):
            commodity_obj = models.Commodity.objects.get(commodity_id=commodity_id)

            if not qr_already_generated(commodity_id, expiry_date):
                models.LocalHarvestDetail(
                    local_harvest=local_harvest,
                    commodity=commodity_obj,
                    batch=batch,
                    expiry_date=expiry_date,
                    quantity=quantity,
                ).save()

                qr_data = generate_qr_data(
                    str(commodity_obj),
                    expiry_date,
                    quantity
                )
                qr_image = generate_qr_image(qr_data)

                response = HttpResponse(qr_image.getvalue(), content_type="image/png")
                response['Content-Disposition'] = (
                    f'attachment; filename="qr_{commodity_obj.commodity_name}_'
                    f'{commodity_obj.grade_id.grade_name}_{expiry_date}.png"'
                )
                return response
            else:
                models.LocalHarvestDetail(
                    local_harvest=local_harvest,
                    commodity=commodity_obj,
                    batch=batch,
                    expiry_date=expiry_date,
                    quantity=quantity,
                ).save()

                messages.warning(
                    request,
                    f"QR not created because data {commodity_id} with expiry {expiry_date} already exists."
                )

        # log activity
        first_commodity = models.Commodity.objects.get(commodity_id=commodity_list[0])
        models.ActivityLog(
            user=request.user,
            action="Add Local Harvest",
            description=f"Added local harvest on {harvest_date} for commodity {first_commodity.commodity_name} - {first_commodity.grade.grade_name}"
        ).save()

        messages.success(request, "Local Harvest successfully added!")
        return redirect("total_commodities")


@login_required(login_url="login")
@role_required(["owner", "inspection"])
def update_local_harvest(request, id):
    try:
        detail_obj = models.LocalHarvestDetail.objects.get(local_harvest_detail_id=id)
    except models.LocalHarvestDetail.DoesNotExist:
        messages.error(request, "Local Harvest data not found!")
        return redirect('read_local_harvest')

    all_commodities = models.Commodity.objects.all()

    if request.method == "GET":
        harvest_date = detail_obj.local_harvest_id.harvest_date.strftime('%Y-%m-%d')
        expiry_date = detail_obj.expiry_date.strftime('%Y-%m-%d')
        return render(request, 'harvest/local/update_local_harvest.html', {
            'detail_obj': detail_obj,
            'all_commodities': all_commodities,
            'harvest_date': harvest_date,
            'expiry_date': expiry_date
        })
    else:
        commodity_obj = models.Commodity.objects.get(commodity_id=request.POST["commodity"])

        detail_obj.local_harvest_id.harvest_date = request.POST["harvest_date"]
        detail_obj.commodity_id = commodity_obj
        detail_obj.batch = request.POST["batch"]
        detail_obj.expiry_date = request.POST["expiry_date"]
        detail_obj.quantity = request.POST["quantity"]

        detail_obj.local_harvest_id.save()
        detail_obj.save()

        models.ActivityLog(
            user=request.user,
            action="Update Local Harvest",
            description=f"Updated local harvest on {detail_obj.local_harvest_id.harvest_date} for commodity {commodity_obj.commodity_name} - {commodity_obj.grade.grade_name}"
        ).save()

        messages.success(request, "Local Harvest updated successfully!")
        return redirect('read_local_harvest')


@login_required(login_url="login")
@role_required(["owner"])
def delete_local_harvest(request, id):
    try:
        detail_obj = models.LocalHarvestDetail.objects.get(local_harvest_detail_id=id)
    except models.LocalHarvestDetail.DoesNotExist:
        messages.error(request, "Local Harvest data not found!")
        return redirect('read_local_harvest')

    models.ActivityLog(
        user=request.user,
        action="Delete Local Harvest",
        description=f"Deleted local harvest on {detail_obj.local_harvest_id.harvest_date} for commodity {detail_obj.commodity.commodity_name} - {detail_obj.commodity.grade.grade_name}"
    ).save()

    detail_obj.delete()
    messages.success(request, "Local Harvest deleted successfully!")
    return redirect('read_local_harvest')

'''READ HARVEST WEIGHT (PARTNER)'''
@login_required(login_url="login")
@role_required(["owner", "admin", "inspection"]) 
def read_partner_weight(request):
    detail_obj = models.PartnerHarvestDetail.objects.values(
        'partner_harvest_id__partner_id__partner_name',
        'commodity_id__commodity_name',
        'commodity_id__grade_id__grade_name',
        'partner_harvest_id__harvest_date',
        'expiry_date'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('partner_harvest_id__harvest_date')

    if not detail_obj.exists():
        messages.error(request, "No Partner Harvest Weight Data Found!")

    return render(request, 'harvest/weight/read_partner_weight.html', {
        'weights': detail_obj,
    })


'''READ HARVEST WEIGHT (LOCAL)'''
@login_required(login_url="login")
@role_required(["owner", "admin", "inspection"]) 
def read_local_weight(request):
    detail_obj = models.LocalHarvestDetail.objects.values(
        'commodity_id__commodity_id_name',
        'commodity_id__grade_id__grade_name',
        'local_harvest_id__harvest_date',
        'expiry_date'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('local_harvest_id__harvest_date')

    if not detail_obj.exists():
        messages.error(request, "No Local Harvest Weight Data Found!")

    return render(request, 'harvest/weight/read_local_weight.html', {
        'weights': detail_obj,
    })


'''CRUD COST TYPE'''
@login_required(login_url="login")
@role_required(["owner", "admin"]) 
def read_cost_type(request):
    cost_types = models.CostType.objects.all()
    if not cost_types.exists():
        messages.error(request, "No Cost Type Data Found")

    return render(request, 'cost/type/read_cost_type.html', {
        'cost_types': cost_types
    })


@login_required(login_url="login")
@role_required(["owner"]) 
def create_cost_type(request):
    if request.method == "GET":
        return render(request, 'cost/type/create_cost_type.html')
    else:
        cost_type_name = request.POST["cost_type_name"]
        cost_type_obj = models.CostType.objects.filter(cost_type_name=cost_type_name)

        if cost_type_obj.exists():
            messages.error(request, "Cost Type Already Exists")
        else:
            models.CostType(cost_type_name=cost_type_name).save()
            messages.success(request, "Cost Type Added Successfully!")

        return redirect("read_cost_type")


@login_required(login_url="login")
@role_required(["owner"]) 
def update_cost_type(request, id):
    try:
        cost_type_obj = models.CostType.objects.get(cost_type_id=id)
    except models.CostType.DoesNotExist:
        messages.error(request, "Cost Type Not Found!")
        return redirect("read_cost_type")

    if request.method == "GET":
        return render(request, 'cost/type/update_cost_type.html', {
            'cost_type': cost_type_obj
        })
    else:
        cost_type_name = request.POST["cost_type_name"]
        if models.CostType.objects.filter(cost_type_name=cost_type_name).exclude(cost_type_id=id).exists():
            messages.error(request, "Cost Type Name Already Exists!")
            return redirect('read_cost_type')

        cost_type_obj.cost_type_name = cost_type_name
        cost_type_obj.save()
        messages.success(request, "Cost Type Updated Successfully!")
        return redirect("read_cost_type")


@login_required(login_url="login")
@role_required(["owner"]) 
def delete_cost_type(request, id):
    try:
        cost_type_obj = models.CostType.objects.get(cost_type_id=id)
        cost_type_obj.delete()
        messages.success(request, "Cost Type Deleted Successfully")
    except models.CostType.DoesNotExist:
        messages.error(request, "Cost Type Not Found!")

    return redirect('read_cost_type')


'''CRUD COST DETAIL'''
@login_required(login_url="login")
@role_required(["owner", "admin", "production"])
def read_cost_detail(request):
    cost_obj = models.Cost.objects.all().order_by('date')
    if not cost_obj.exists():
        messages.error(request, "No Cost Detail Data Found!")

    return render(request, 'cost/detail/read_cost_detail.html', {
        'cost_obj': cost_obj
    })


@login_required(login_url="login")
@role_required(["owner", "admin", "production"]) 
def create_cost_detail(request):
    all_cost_types = models.CostType.objects.all()
    if request.method == "GET":
        return render(request, 'cost/detail/create_cost_detail.html', {
            'all_cost_types': all_cost_types
        })
    else:
        cost_type_name = request.POST["cost_type_name"]
        date = request.POST['date']
        cost_name = request.POST['cost_name']
        cost_amount = request.POST['cost_amount']

        cost_type = models.CostType.objects.get(cost_type_name=cost_type_name)

        models.Cost(
            cost_type_id=cost_type,
            date=date,
            cost_name=cost_name,
            cost_amount=cost_amount
        ).save()

        messages.success(request, "Cost Detail Added Successfully")
        return redirect("read_cost_detail")


@login_required(login_url="login")
@role_required(["owner", "admin", "production"])    
def update_cost_detail(request, id):
    try:
        cost_detail_obj = models.Cost.objects.get(cost_id=id)
    except models.Cost.DoesNotExist:
        messages.error(request, "Cost Detail Not Found!")
        return redirect('read_cost_detail')
  
    all_cost_types = models.CostType.objects.all()
  
    if request.method == "GET":
        date = cost_detail_obj.date.strftime('%Y-%m-%d')  # format date
        return render(request, 'cost/detail/update_cost_detail.html', {
            'cost_detail': cost_detail_obj,
            'all_cost_types': all_cost_types,
            'date': date,
        })
    else:    
        cost_type = models.CostType.objects.get(cost_type_name=request.POST["cost_type_name"])

        cost_detail_obj.cost_type_id = cost_type
        cost_detail_obj.date = request.POST['date']
        cost_detail_obj.cost_name = request.POST["cost_name"]
        cost_detail_obj.cost_amount = request.POST["cost_amount"]

        cost_detail_obj.save()
        
        messages.success(request, "Cost Detail Updated Successfully!")
        return redirect('read_cost_detail')
    

@login_required(login_url="login")
@role_required(["owner"])    
def delete_cost_detail(request, id):
    try:
        cost_detail_obj = models.Cost.objects.get(cost_detail_id=id)
        cost_detail_obj.delete()
        messages.success(request, "Cost Detail Deleted Successfully!")
    except models.Cost.DoesNotExist:
        messages.error(request, "Cost Detail Not Found!")

    return redirect('read_cost_detail')



'''CRUD PRODUCTION'''
@login_required(login_url="login")
@role_required(["owner", "admin", "production"]) 
def read_production(request):
    production_details = models.ProductionDetail.objects.all()
    if not production_details.exists():
        messages.error(request, "No Production Data Found!")

    return render(request, "production/read_production.html", {
        'production_details': production_details
    })


@login_required(login_url="login")
@role_required(["owner", "admin", "production"]) 
def create_production(request):
    products = models.Product.objects.all()
    if request.method == 'GET':
        return render(request, "production/create_production.html", {
            'products': products
        })
    else:
        date = request.POST['date']
        product_status_list = request.POST.getlist('product_status')
        product_list = request.POST.getlist('product_id')
        quantity_list = request.POST.getlist('product_quantity')

        production = models.Production(
            date=date,
        )
        production.save()

        log_products = []
        log_quantities = []
        
        for status, product_id, quantity in zip(product_status_list, product_list, quantity_list):
            product_obj = models.Product.objects.get(product_id=product_id)
            models.ProductionDetail(
                product_id=product_obj,
                production_id=production,
                product_quantity=quantity,
                product_status=status
            ).save()
            log_products.append(f"{product_obj.product_name}")
            log_quantities.append(f"{quantity}")
        
        log_description = f"Added production on {date}:\n"
        for prod, qty in zip(log_products, log_quantities):
            log_description += f"- Product: {prod}, Quantity: {qty}\n"

        models.ActivityLog(
            user=request.user,
            action="Add Production",
            description=log_description.strip()
        ).save()
        print("STATUS LIST:", product_status_list)
        print("PRODUCT LIST:", product_list)
        print("QUANTITY LIST:", quantity_list)
        messages.success(request, "Production Data Saved Successfully!")
        return redirect("read_production")


''' UPDATE & DELETE PRODUCTION '''
@login_required(login_url="login")
@role_required(["owner", "admin", "production"])   
def update_production(request, id):
    production_detail = models.ProductionDetail.objects.get(production_detail_id=id)
    products = models.Product.objects.all()

    if request.method == 'GET':
        date = production_detail.production_id.date.strftime('%Y-%m-%d')
        return render(request, "production/update_production.html", {
            'production_detail': production_detail,
            'products': products,
            'date': date
        })
    else:
        product_obj = models.Product.objects.get(product_id=request.POST['product'])
        
        old_product = production_detail.product_id.product_name
        old_quantity = production_detail.product_quantity
        old_status = production_detail.product_status
        old_date = production_detail.production_id.date.strftime('%Y-%m-%d')

        new_date = request.POST['date']
        new_status = request.POST['product_status']
        new_quantity = request.POST['quantity']

        production_detail.production_id.date = new_date
        production_detail.product_status = new_status
        production_detail.product_id = product_obj
        production_detail.product_quantity = new_quantity
        production_detail.production_id.save()
        production_detail.save()
        
        models.ActivityLog.objects.create(
            user=request.user,
            action="Update Production",
            description=(
                f"Updated production from {old_date} to {new_date}:\n"
                f"- Product: {old_product} → {product_obj.product_name}\n"
                f"- Quantity: {old_quantity} → {new_quantity}\n"
                f"- Status: {old_status} → {new_status}"
            )
        )

        messages.success(request, "Production data updated successfully!")
        return redirect('read_production')
    

@login_required(login_url="login")
@role_required(["owner"])      
def delete_production(request, id):
    production_detail = models.ProductionDetail.objects.get(production_detail_id=id)
    product_name = production_detail.product_id.product_name
    quantity = production_detail.product_quantity
    date = production_detail.production_id.date.strftime('%Y-%m-%d')

    production_detail.delete()

    models.ActivityLog.objects.create(
        user=request.user,
        action="Delete Production",
        description=f"Deleted production on {date} for product {product_name} with quantity {quantity} units."
    )
    messages.success(request, "Production data deleted successfully!")
    return redirect('read_production')


''' HARVEST REPORT '''
@login_required(login_url="login")
@role_required(["owner"]) 
def harvest_report(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    harvest_type = request.GET.get('harvest_type')

    if start and end:
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")

        if harvest_type == 'local harvest':
            harvest_local = models.LocalHarvest.objects.filter(date__range=(start, end)).order_by('harvest_date')
            detail_local = []
            total_list = []

            for item in harvest_local:
                detail_list = []
                purchase_prices = []
                harvest_id = item.local_harvest_id

                harvest_details = models.LocalHarvestDetail.objects.filter(harvest_local=harvest_id)
                if not harvest_details.exists():
                    continue

                for detail in harvest_details:
                    purchase_price = detail.commodity_id.purchase_price * detail.quantity
                    purchase_prices.append(purchase_price)

                total_purchase = sum(purchase_prices)
                detail_list.extend([item, harvest_details, purchase_prices, total_purchase])

                total_list.append(total_purchase)
                detail_local.append(detail_list)

            grand_total_local = sum(total_list)

            return render(request, 'report/harvest_report.html', {
                'detail_local': detail_local,
                'grand_total_local': grand_total_local,
                'start': start_date,
                'end': end_date,
                'harvest_type': harvest_type
            })

        else:  # partner harvest
            harvest_partner = models.PartnerHarvest.objects.filter(date__range=(start, end)).order_by('harvest_date')
            detail_partner = []
            total_list = []

            for item in harvest_partner:
                detail_list = []
                purchase_prices = []
                harvest_id = item.partner_harvest_id

                harvest_details = models.PartnerHarvestDetail.objects.filter(partner_harvest_id=harvest_id)
                if not harvest_details.exists():
                    continue

                for detail in harvest_details:
                    purchase_price = detail.commodity_id.purchase_price * detail.quantity
                    purchase_prices.append(purchase_price)

                total_purchase = sum(purchase_prices)
                detail_list.extend([item, harvest_details, purchase_prices, total_purchase])

                total_list.append(total_purchase)
                detail_partner.append(detail_list)

            grand_total = sum(total_list)

            return render(request, 'report/harvest_report.html', {
                'detail_partner': detail_partner,
                'grand_total': grand_total,
                'start': start_date,
                'end': end_date,
                'harvest_type': harvest_type
            })

    else:
        if harvest_type == 'local harvest':
            harvest_local = models.LocalHarvest.objects.all().order_by('harvest_date')
            detail_local = []
            total_list = []

            for item in harvest_local:
                detail_list = []
                purchase_prices = []
                harvest_id = item.local_harvest_id

                harvest_details = models.LocalHarvestDetail.objects.filter(harvest_local=harvest_id)
                if not harvest_details.exists():
                    continue

                for detail in harvest_details:
                    purchase_price = detail.commodity_id.purchase_price * detail.quantity
                    purchase_prices.append(purchase_price)

                total_purchase = sum(purchase_prices)
                detail_list.extend([item, harvest_details, purchase_prices, total_purchase])

                total_list.append(total_purchase)
                detail_local.append(detail_list)

            grand_total_local = sum(total_list)

            return render(request, 'report/harvest_report.html', {
                'detail_local': detail_local,
                'grand_total_local': grand_total_local,
                'harvest_type': harvest_type
            })

        else:  # partner harvest
            harvest_type = 'partner harvest'
            harvest_partner = models.PartnerHarvest.objects.all().order_by('harvest_date')
            detail_partner = []
            total_list = []

            for item in harvest_partner:
                detail_list = []
                purchase_prices = []
                harvest_id = item.partner_harvest_id

                harvest_details = models.PartnerHarvestDetail.objects.filter(partner_harvest_id=harvest_id)
                if not harvest_details.exists():
                    continue

                for detail in harvest_details:
                    purchase_price = detail.commodity_id.purchase_price * detail.quantity
                    purchase_prices.append(purchase_price)

                total_purchase = sum(purchase_prices)
                detail_list.extend([item, harvest_details, purchase_prices, total_purchase])

                total_list.append(total_purchase)
                detail_partner.append(detail_list)

            grand_total = sum(total_list)

            return render(request, 'report/harvest_report.html', {
                'detail_partner': detail_partner,
                'grand_total': grand_total,
                'harvest_type': harvest_type
            })
            
@login_required(login_url="login")
@role_required(["owner"]) 
def profit_and_loss_report(request):
    if len(request.GET) == 0:
        return render(request, 'report/pnl_report.html')
    else:
        month_str = request.GET['bulan']
        year, month = map(int, month_str.split('-'))

        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, calendar.monthrange(year, month)[1])

        total_sales_list = []
        hpp_temp_list = []
        wip_start = {}
        wip_end = {}
        fg_start = {}
        fg_end = {}

        # SALES DETAIL
        sales_detail = models.SaleDetail.objects.filter(
            sale_id__date__range=(start_date, end_date)
        )

        if not sales_detail.exists():
            total_sales_list.append(0)
        else:
            for item in sales_detail:
                try:
                    commodity_qty = item.commodity_quantity
                    product_qty = item.product_quantity
                    commodity_price = item.commodity_id.selling_price if item.commodity_id else None
                    product_price = item.product_id.product_price if item.product_id else None

                    if commodity_qty is None or product_qty is None or commodity_price is None or product_price is None:
                        continue

                    total = commodity_qty * commodity_price + product_qty * product_price
                    total_sales_list.append(total)

                except AttributeError as e:
                    print(f"Error processing SaleDetail {item.sale_detail_id}: {e}")
                    continue

        # COST OF GOODS SOLD (COGS) from Production
        products = models.Product.objects.all()
        for product in products:
            product_name = product.product_name

            # commodity conversion (this part depends on your conversion mapping!)
            if product_name not in product_to_commodity:
                continue

            commodity_name = product_to_commodity[product_name][0]
            conversion_rate = product_to_commodity[product_name][1]

            commodity_price_qs = models.Commodity.objects.filter(
                commodity_name=commodity_name,
                grade_id__grade_name="processed"
            ).values("purchase_price")

            if not commodity_price_qs.exists():
                commodity_price = 0
            else:
                commodity_price = commodity_price_qs[0]['purchase_price']

            production_details_fg = models.ProductionDetail.objects.filter(
                product_id__product_name=product_name, product_status="fg"
            )

            conversion_result = 0
            for detail in production_details_fg:
                conversion_result += math.ceil(detail.product_quantity * conversion_rate)

            # WIP & FG balances
            wip_start_qs = models.ProductionDetail.objects.filter(
                product_id__product_name=product_name,
                product_status="wip",
                production_id__date=start_date
            )
            wip_end_qs = models.ProductionDetail.objects.filter(
                product_id__product_name=product_name,
                product_status="wip",
                production_id__date=end_date
            )
            fg_start_qs = models.ProductionDetail.objects.filter(
                product_id__product_name=product_name,
                product_status="fg",
                production_id__date=start_date
            )
            fg_end_qs = models.ProductionDetail.objects.filter(
                product_id__product_name=product_name,
                product_status="fg",
                production_id__date=end_date
            )

            # Calculate WIP start
            for d in wip_start_qs:
                cost = d.product_quantity * d.product_id.product_price
                wip_start[product_name] = wip_start.get(product_name, 0) + cost

            # Calculate WIP end
            for d in wip_end_qs:
                cost = d.product_quantity * d.product_id.product_price
                wip_end[product_name] = wip_end.get(product_name, 0) + cost

            # Calculate FG start
            for d in fg_start_qs:
                cost = d.product_quantity * d.product_id.product_price
                fg_start[product_name] = fg_start.get(product_name, 0) + cost

            # Calculate FG end
            for d in fg_end_qs:
                cost = d.product_quantity * d.product_id.product_price
                fg_end[product_name] = fg_end.get(product_name, 0) + cost

            wip_start_val = wip_start.get(product_name, 0)
            wip_end_val = wip_end.get(product_name, 0)

            hpp_temp = (conversion_result * commodity_price) + wip_start_val - wip_end_val
            hpp_temp_list.append(hpp_temp)

        # LABOR & OVERHEAD COSTS
        labor_overhead_costs = models.Cost.objects.filter(
            Q(cost_type_id__cost_type_name="Labor Cost") |
            Q(cost_type_id__cost_type_name="Overhead Cost"),
            date__range=(start_date, end_date)
        )
        if not labor_overhead_costs.exists():
            total_costs = {'total': 0}
        else:
            total_costs = labor_overhead_costs.aggregate(total=Sum('cost_amount'))

        hpp_final = sum(hpp_temp_list) + total_costs['total']

        fg_start_total = sum(fg_start.values())
        fg_end_total = sum(fg_end.values())

        # Raw Commodity Purchases (Partner & Local)
        commodities = models.Commodity.objects.exclude(grade_id__grade_name="processed")

        partner_purchase_list = []
        local_purchase_list = []

        for c in commodities:
            partner_details = models.PartnerHarvestDetail.objects.filter(commodity_id=c)
            local_details = models.LocalHarvestDetail.objects.filter(commodity_id=c)

            for d in partner_details:
                cost = d.quantity * d.commodity_id.purchase_price
                partner_purchase_list.append(cost)

            for d in local_details:
                cost = d.quantity * d.commodity_id.purchase_price
                local_purchase_list.append(cost)

        # Final COGS
        cogs = hpp_final + sum(partner_purchase_list) + sum(local_purchase_list) + fg_start_total - fg_end_total

        # Gross Profit
        total_revenue = sum(total_sales_list)
        gross_profit = total_revenue - cogs

        # Income Tax (0.5%)
        income_tax = (0.5 / 100) * gross_profit

        # Operating Expenses
        operating_expenses = models.Cost.objects.filter(
            date__range=(start_date, end_date),
            cost_type_id__cost_type_name="Operating Expense"
        )
        operating_expense_dict = {}
        for c in operating_expenses:
            if c.cost_name in operating_expense_dict:
                operating_expense_dict[c.cost_name] += c.cost_amount
            else:
                operating_expense_dict[c.cost_name] = c.cost_amount

        total_operating_expenses = sum(operating_expense_dict.values())

        # Net Income
        net_income = gross_profit - income_tax - total_operating_expenses
        if net_income < 0:
            messages.warning(request, "Net income is negative!")

        return render(
            request, 'report/pnl_report.html', {
                'month': month_str,
                'start_date': start_date,
                'end_date': end_date,
                'total_revenue': total_revenue,
                'production_cogs': hpp_final,
                'sales_cogs': cogs,
                'gross_profit': gross_profit,
                'income_tax': income_tax,
                'operating_expenses': operating_expense_dict,
                'total_operating_expenses': total_operating_expenses,
                'net_income': net_income
            }
        )

@login_required(login_url="login")
@role_required(["owner"])
def profit_and_loss_pdf(request, month):
    year, month = map(int, month.split('-'))
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, calendar.monthrange(year, month)[1])

    total_sales_list = []
    hpp_temp_list = []
    wip_start = {}
    wip_end = {}
    fg_start = {}
    fg_end = {}

    # SALES DETAIL
    sales_detail = models.SaleDetail.objects.filter(
        sale_id__date__range=(start_date, end_date)
    )

    if not sales_detail.exists():
        total_sales_list.append(0)
    else:
        for item in sales_detail:
            try:
                commodity_qty = item.commodity_quantity
                product_qty = item.product_quantity
                commodity_price = item.commodity_id.selling_price if item.commodity_id else None
                product_price = item.product_id.product_price if item.product_id else None

                if commodity_qty is None or product_qty is None or commodity_price is None or product_price is None:
                    continue

                total = commodity_qty * commodity_price + product_qty * product_price
                total_sales_list.append(total)

            except AttributeError as e:
                print(f"Error processing SaleDetail {item.sale_detail_id}: {e}")
                continue

    # COST OF GOODS SOLD (Production COGS)
    products = models.Product.objects.all()
    for product in products:
        product_name = product.product_name

        if product_name not in product_to_commodity:
            continue

        commodity_name = product_to_commodity[product_name][0]
        conversion_rate = product_to_commodity[product_name][1]

        commodity_price_qs = models.Commodity.objects.filter(
            commodity_name=commodity_name,
            grade_id__grade_name="processed"
        ).values("purchase_price")

        commodity_price = 0 if not commodity_price_qs.exists() else commodity_price_qs[0]['purchase_price']

        production_details_fg = models.ProductionDetail.objects.filter(
            product_id__product_name=product_name,
            product_status="fg"
        )

        conversion_result = 0
        for detail in production_details_fg:
            conversion_result += math.ceil(detail.product_quantity * conversion_rate)

        # WIP & FG balances
        wip_start_qs = models.ProductionDetail.objects.filter(
            product_id__product_name=product_name,
            product_status="wip",
            production_id__date=start_date
        )
        wip_end_qs = models.ProductionDetail.objects.filter(
            product_id__product_name=product_name,
            product_status="wip",
            production_id__date=end_date
        )
        fg_start_qs = models.ProductionDetail.objects.filter(
            product_id__product_name=product_name,
            product_status="fg",
            production_id__date=start_date
        )
        fg_end_qs = models.ProductionDetail.objects.filter(
            product_id__product_name=product_name,
            product_status="fg",
            production_id__date=end_date
        )

        # Calculate WIP start
        for d in wip_start_qs:
            cost = d.product_quantity * d.product_id.product_price
            wip_start[product_name] = wip_start.get(product_name, 0) + cost

        # Calculate WIP end
        for d in wip_end_qs:
            cost = d.product_quantity * d.product_id.product_price
            wip_end[product_name] = wip_end.get(product_name, 0) + cost

        # Calculate FG start
        for d in fg_start_qs:
            cost = d.product_quantity * d.product_id.product_price
            fg_start[product_name] = fg_start.get(product_name, 0) + cost

        # Calculate FG end
        for d in fg_end_qs:
            cost = d.product_quantity * d.product_id.product_price
            fg_end[product_name] = fg_end.get(product_name, 0) + cost

        wip_start_val = wip_start.get(product_name, 0)
        wip_end_val = wip_end.get(product_name, 0)

        hpp_temp = (conversion_result * commodity_price) + wip_start_val - wip_end_val
        hpp_temp_list.append(hpp_temp)

    # LABOR & OVERHEAD COSTS
    labor_overhead_costs = models.Cost.objects.filter(
        Q(cost_type_id__cost_type_name="Labor Cost") |
        Q(cost_type_id__cost_type_name="Overhead Cost"),
        date__range=(start_date, end_date)
    )
    if not labor_overhead_costs.exists():
        total_costs = {'total': 0}
    else:
        total_costs = labor_overhead_costs.aggregate(total=Sum('cost_amount'))

    hpp_final = sum(hpp_temp_list) + total_costs['total']

    fg_start_total = sum(fg_start.values())
    fg_end_total = sum(fg_end.values())

    # Raw Commodity Purchases (Partner & Local)
    commodities = models.Commodity.objects.exclude(grade_id__grade_name="processed")

    partner_purchase_list = []
    local_purchase_list = []

    for c in commodities:
        partner_details = models.PartnerHarvestDetail.objects.filter(commodity_id=c)
        local_details = models.LocalHarvestDetail.objects.filter(commodity_id=c)

        for d in partner_details:
            cost = d.quantity * d.commodity_id.purchase_price
            partner_purchase_list.append(cost)

        for d in local_details:
            cost = d.quantity * d.commodity_id.purchase_price
            local_purchase_list.append(cost)

    # Final COGS
    cogs = hpp_final + sum(partner_purchase_list) + sum(local_purchase_list) + fg_start_total - fg_end_total

    # Gross Profit
    total_revenue = sum(total_sales_list)
    gross_profit = total_revenue - cogs

    # Income Tax (0.5%)
    income_tax = (0.5 / 100) * gross_profit

    # Operating Expenses
    operating_expenses = models.Cost.objects.filter(
        date__range=(start_date, end_date),
        cost_type_id__cost_type_name="Operating Expense"
    )
    operating_expense_dict = {}
    for c in operating_expenses:
        if c.cost_name in operating_expense_dict:
            operating_expense_dict[c.cost_name] += c.cost_amount
        else:
            operating_expense_dict[c.cost_name] = c.cost_amount

    total_operating_expenses = sum(operating_expense_dict.values())

    # Net Income
    net_income = gross_profit - income_tax - total_operating_expenses

    response = HttpResponse(content_type='application/pdf;')
    response['Content-Disposition'] = 'inline; filename=profit_and_loss.pdf'
    response['Content-Transfer-Encoding'] = 'binary'
    html_string = render_to_string(
        'report/pnl_report_pdf.html', {
            'month': month,
            'total_revenue': total_revenue,
            'production_cogs': hpp_final,
            'sales_cogs': cogs,
            'gross_profit': gross_profit,
            'income_tax': income_tax,
            'operating_expenses': operating_expense_dict,
            'total_operating_expenses': total_operating_expenses,
            'net_income': net_income
        })

    html = HTML(string=html_string)
    result = html.write_pdf()

    with tempfile.NamedTemporaryFile(delete=True) as output:
        output.write(result)
        output.flush()
        output.seek(0)
        response.write(output.read())

    return response

@login_required(login_url="login")
@role_required(["owner"])
def monthly_harvest_report(request):
    today = now().date()
    start_of_month = today.replace(day=1)

    if today.month == 12:
        start_of_next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        start_of_next_month = today.replace(month=today.month + 1, day=1)

    all_partners = models.Partner.objects.all()

    for partner in all_partners:
        monthly_harvests = models.PartnerHarvest.objects.filter(
            partner=partner,
            harvest_date__gte=start_of_month,
            harvest_date__lt=start_of_next_month
        )

        detail_data = []
        total_quantity = 0

        for harvest in monthly_harvests:
            details = models.PartnerHarvestDetail.objects.filter(partner_harvest=harvest).select_related("commodity")
            for detail in details:
                detail_data.append({
                    'harvest_date': harvest.harvest_date,
                    'commodity_name': detail.commodity_id.commodity_name,
                    'quantity': detail.quantity,
                })
                total_quantity += detail.quantity

        if total_quantity < partner.min_quantity:
            subject = f"Monthly Harvest Report - {partner.partner_name}"
            html_message = render_to_string("email_report.html", {
                'partner_name': partner.partner_name,
                'details': detail_data,
                'total': total_quantity,
                'minimum_quantity': partner.min_quantity,
            })

            email = EmailMessage(subject, html_message, settings.EMAIL_HOST_USER, [partner.email])
            email.content_subtype = "html"
            email.send()

    return render(request, '404.html')


@login_required(login_url="login")
def total_commodities(request):
    if request.method == "GET":
        partner_harvests = models.PartnerHarvest.objects.all()
        local_harvests = models.LocalHarvest.objects.all()

        results = {}
        commodity_set = set()
        batch_set = set()
        harvest_date_set = set()
        expiry_date_set = set()

        def process_harvest(harvest_list, is_partner=True):
            for harvest in harvest_list:
                details = (
                    models.PartnerHarvestDetail.objects.filter(partner_harvest_id=harvest)
                    if is_partner else
                    models.LocalHarvestDetail.objects.filter(local_harvest_id=harvest)
                )

                for detail in details:
                    commodity_obj = detail.commodity_id
                    commodity_str = str(commodity_obj)
                    batch = detail.batch
                    harvest_date = (
                        detail.partner_harvest_id.harvest_date
                        if is_partner else
                        detail.local_harvest_id.harvest_date
                    )
                    expiry_date = detail.expiry_date
                    quantity = detail.quantity

                    key = (commodity_str, batch, harvest_date, expiry_date)

                    if key not in results:
                        data_qr = generate_qr_data(commodity_str, expiry_date, quantity)
                        qr_img = generate_qr_image(data_qr)
                        results[key] = {"total": quantity, "qr": qr_img}
                    else:
                        results[key]["total"] += quantity

                    commodity_set.add(commodity_str)
                    batch_set.add(batch)
                    harvest_date_set.add(harvest_date)
                    expiry_date_set.add(expiry_date)

        process_harvest(partner_harvests, is_partner=True)
        process_harvest(local_harvests, is_partner=False)

        result_list = [
            {
                "commodity": commodity,
                "batch": batch,
                "harvest_date": harvest_date.strftime("%Y-%m-%d"),
                "expiry_date": expiry_date.strftime("%Y-%m-%d"),
                "total_quantity": data["total"],
                "qr": data["qr"]
            }
            for (commodity, batch, harvest_date, expiry_date), data in results.items()
        ]

        return render(request, "total_commodities.html", {
            "total_list": result_list,
            "commodity_list": sorted(commodity_set),
            "batch_list": sorted(batch_set),
            "harvest_date_list": sorted(harvest_date_set),
            "expiry_date_list": sorted(expiry_date_set)
        })


def generate_qr_image(data):
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer


def generate_qr_data(commodity_str, expiry_date, quantity):
    return f"{commodity_str}|{expiry_date}|{quantity}"


def qr_already_generated(commodity_id, expiry_date):
    return (
        models.LocalHarvestDetail.objects.filter(
            commodity_id=commodity_id,
            expiry_date=expiry_date
        ).exists()
        or models.PartnerHarvestDetail.objects.filter(
            commodity_id=commodity_id,
            expiry_date=expiry_date
        ).exists()
    )


@login_required(login_url="login")
def activity_logs(request):
    logs = models.ActivityLog.objects.all().order_by('-timestamp') 
    return render(request, 'log/activity_log.html', {'logs': logs})

@login_required
@role_required(['owner'])  
def delete_log(request, id):
    try:
        log = models.ActivityLog.objects.get(id=id)
        log.delete()
        messages.success(request, "Log berhasil dihapus.")
    except models.ActivityLog.DoesNotExist:
        messages.error(request, "Log tidak ditemukan.")
    return redirect('activity_logs') 

