from django.contrib import admin
from . import models
# Register your models here.
admin.site.register(models.Partner)
admin.site.register(models.Grade)
admin.site.register(models.Commodity)
admin.site.register(models.Product)
admin.site.register(models.PartnerHarvest)
admin.site.register(models.LocalHarvestDetail)
admin.site.register(models.LocalHarvest)
admin.site.register(models.PartnerHarvestDetail)
admin.site.register(models.Market)
admin.site.register(models.Sale)
admin.site.register(models.SaleDetail)
admin.site.register(models.Production)
admin.site.register(models.ProductionDetail)
admin.site.register(models.CostType)
admin.site.register(models.Cost)