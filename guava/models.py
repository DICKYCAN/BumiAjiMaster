from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Partner(models.Model):
    partner_id = models.AutoField(primary_key=True)
    partner_name = models.CharField(max_length=100)
    partner_address = models.TextField(blank=True, null=True)
    partner_phone = models.PositiveBigIntegerField()
    start_date = models.DateField()
    contract_duration = models.PositiveIntegerField()
    land_area = models.PositiveIntegerField(null=True)
    partner_status = models.BooleanField(default=None, null=True)
    min_quantity = models.PositiveIntegerField()
    email = models.EmailField()

    def __str__(self):
        return str(self.partner_name)


class Grade(models.Model):
    grade_id = models.AutoField(primary_key=True)
    grade_name = models.CharField(max_length=100)
    grade_description = models.TextField(blank=True, null=True)

    def __str__(self):
        return str(self.grade_name)


class Commodity(models.Model):
    commodity_id = models.AutoField(primary_key=True)
    grade_id = models.ForeignKey(Grade, on_delete=models.CASCADE)
    commodity_name = models.CharField(max_length=100)
    purchase_price = models.IntegerField()
    selling_price = models.IntegerField()

    def __str__(self):
        return f"{self.commodity_name} - {self.grade_id.grade_name}"


class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=100)
    product_unit = models.CharField(max_length=100)
    product_price = models.PositiveIntegerField()

    def __str__(self):
        return str(self.product_name)


class PartnerHarvest(models.Model):
    partner_harvest_id = models.AutoField(primary_key=True)
    partner_id = models.ForeignKey(Partner, on_delete=models.CASCADE)
    harvest_date = models.DateField()

    def __str__(self):
        return str(self.partner_id.partner_name)


class PartnerHarvestDetail(models.Model):
    partner_harvest_detail_id = models.AutoField(primary_key=True)
    partner_harvest_id = models.ForeignKey(PartnerHarvest, on_delete=models.CASCADE)
    commodity_id = models.ForeignKey(Commodity, on_delete=models.CASCADE)
    batch = models.PositiveIntegerField()
    expiry_date = models.DateField()
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return "{} - {}".format(self.partner_harvest_id, self.batch)


class LocalHarvest(models.Model):
    local_harvest_id = models.AutoField(primary_key=True)
    harvest_date = models.DateField()

    def __str__(self):
        return str(self.local_harvest_id)


class LocalHarvestDetail(models.Model):
    local_harvest_detail_id = models.AutoField(primary_key=True)
    local_harvest_id = models.ForeignKey(LocalHarvest, on_delete=models.CASCADE)
    commodity_id = models.ForeignKey(Commodity, on_delete=models.CASCADE)
    batch = models.PositiveIntegerField()
    expiry_date = models.DateField()
    quantity = models.PositiveIntegerField(null=True)

    def __str__(self):
        return "{} - {}".format(self.local_harvest_id, self.batch)


class Market(models.Model):
    market_id = models.AutoField(primary_key=True)
    market_name = models.CharField(max_length=100)
    market_address = models.TextField(null=True, blank=True)

    def __str__(self):
        return str(self.market_name)


class Sale(models.Model):
    sale_id = models.AutoField(primary_key=True)
    market_id = models.ForeignKey(Market, on_delete=models.CASCADE)
    date = models.DateField()

    def __str__(self):
        return str(self.market_id)


class SaleDetail(models.Model):
    sale_detail_id = models.AutoField(primary_key=True)
    sale_id = models.ForeignKey(Sale, on_delete=models.CASCADE)
    product_id = models.ForeignKey(Product, null=True, on_delete=models.CASCADE)
    commodity_id = models.ForeignKey(Commodity, null=True, on_delete=models.CASCADE)
    commodity_quantity = models.PositiveIntegerField(null=True)
    product_quantity = models.PositiveIntegerField(null=True)

    def __str__(self):
        return str(self.sale_id)


class Production(models.Model):
    production_id = models.AutoField(primary_key=True)
    date = models.DateField()

    def __str__(self):
        return str(self.date)


class ProductionDetail(models.Model):
    production_detail_id = models.AutoField(primary_key=True)
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    production_id = models.ForeignKey(Production, on_delete=models.CASCADE)
    product_quantity = models.PositiveIntegerField()
    product_status = models.CharField(max_length=100, null=True)

    def __str__(self):
        return "{} - {}".format(self.product_id, self.product_status)


class CostType(models.Model):
    cost_type_id = models.AutoField(primary_key=True)
    cost_type_name = models.CharField(max_length=100)

    def __str__(self):
        return str(self.cost_type_name)


class Cost(models.Model):
    cost_id = models.AutoField(primary_key=True)
    cost_type_id = models.ForeignKey(CostType, on_delete=models.CASCADE)
    date = models.DateField()
    cost_name = models.CharField(max_length=100)
    cost_amount = models.PositiveIntegerField()

    def __str__(self):
        return "{} - {}".format(self.cost_type_id, self.cost_name)


class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"
