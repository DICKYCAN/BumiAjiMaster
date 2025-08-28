from django.urls import path
from . import views

urlpatterns = [
    path('',views.login_view, name='login'),
    path('performlogin',views.perform_login,name="performlogin"),
    path('performlogout',views.perform_logout,name="performlogout"),
    path('base', views.base,name='base'),
    # CRUD partner
    path('create_partner', views.create_partner,name='create_partner'),
    path('read_partner', views.read_partner,name='read_partner'),
    path('update_partner/<str:id>', views.update_partner,name='update_partner'),
    path('delete_partner/<str:id>', views.delete_partner,name='delete_partner'),
    # CRUD sale
    path('create_sale', views.create_sale,name='create_sale'),
    path('read_sale', views.read_sale,name='read_sale'),
    path('update_sale/<str:id>', views.update_sale,name='update_sale'),
    path('delete_sale/<str:id>', views.delete_sale,name='delete_sale'),
    # CUD DETAIL sale
    path('update_sale_detail/<str:id>', views.update_sale_detail,name='update_sale_detail'),
    path('delete_sale_detail/<str:id>', views.delete_sale_detail,name='delete_sale_detail'),
    path('create_sale_detail/<str:id>', views.create_sale_detail,name='create_sale_detail'),
    # CRUD product
    path('create_product', views.create_product,name='create_product'),
    path('read_product', views.read_product,name='read_product'),
    path('update_product/<str:id>', views.update_product,name='update_product'),
    path('delete_product/<str:id>', views.delete_product,name='delete_product'),
    # CRUD commodity
    path('create_commodity', views.create_commodity,name='create_commodity'),
    path('read_commodity', views.read_commodity,name='read_commodity'),
    path('update_commodity/<str:id>', views.update_commodity,name='update_commodity'),
    path('delete_commodity/<str:id>', views.delete_commodity,name='delete_commodity'),
    # CRUD GRADE
    path('create_grade', views.create_grade,name='create_grade'),
    path('read_grade',views.read_grade,name='read_grade'),
    path('update_grade/<str:id>', views.update_grade,name='update_grade'),
    path('delete_grade/<str:id>', views.delete_grade,name='delete_grade'),
    # CRUD market
    path('create_market', views.create_market,name='create_market'),
    path('read_market', views.read_market,name='read_market'),
    path('update_market/<str:id>', views.update_market,name='update_market'),
    path('delete_market/<str:id>', views.delete_market,name='delete_market'),
     # CRUD PANEN
    path('create_partner_harvest', views.create_partner_harvest,name='create_partner_harvest'),
    path('read_partner_harvest', views.read_partner_harvest,name='read_partner_harvest'),
    path('update_partner_harvest/<str:id>', views.update_partner_harvest,name='update_partner_harvest'),
    path('delete_partner_harvest/<str:id>', views.delete_partner_harvest,name='delete_partner_harvest'),
    
    path('read_local_harvest', views.read_local_harvest,name='read_local_harvest'),
    path('update_local_harvest/<str:id>', views.update_local_harvest,name='update_local_harvest'),
    path('delete_local_harvest/<str:id>', views.delete_local_harvest,name='delete_local_harvest'),

    path('read_partner_weight', views.read_partner_weight,name='read_partner_weight'),
    path('read_local_weight', views.read_local_weight,name='read_local_weight'),

    # CRUD BIAYA
    path('create_cost_type', views.create_cost_type,name='create_cost_type'),
    path('read_cost_type', views.read_cost_type,name='read_cost_type'),
    path('update_cost_type/<str:id>', views.update_cost_type,name='update_cost_type'),
    path('delete_cost_type/<str:id>', views.delete_cost_type,name='delete_cost_type'),
    
    path('create_cost_detail', views.create_cost_detail,name='create_cost_detail'),
    path('read_cost_detail', views.read_cost_detail,name='read_cost_detail'),
    path('update_cost_detail/<str:id>', views.update_cost_detail,name='update_cost_detail'),
    path('delete_cost_detail/<str:id>', views.delete_cost_detail,name='delete_cost_detail'),

    # CRUD production
    path('create_production', views.create_production,name='create_production'),
    path('read_production', views.read_production,name='read_production'),
    path('update_production/<str:id>', views.update_production,name='update_production'),
    path('delete_production/<str:id>', views.delete_production,name='delete_production'),

    # Laporan
    path('sales_report', views.sales_report,name='sales_report'),
    path('harvest_report', views.harvest_report,name='harvest_report'),
    path('pnl_report', views.profit_and_loss_report,name='pnl_report'),
    path('profit_and_loss_pdf<str:bulan>', views.profit_and_loss_pdf,name='profit_and_loss_pdf'),

    path('total_commodities/', views.total_commodities, name='total_commodities'),
    path('rekap_panen/', views.monthly_harvest_report, name='rekap-panen'),
    path('activity_logs/', views.activity_logs, name='activity_logs'),
    path('logs/delete/<int:id>/', views.delete_log, name='delete_log')



]