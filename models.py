from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

class Products(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, nullable=False)
    quantity_in_stock = fields.IntField(default=0)
    quantity_soft = fields.IntField(default=0)
    unit_price = fields.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    revenue = fields.DecimalField(max_digits=20, decimal_places=2, default=0.00)

    supplied_by = fields.ForeignKeyField("models.Supplier", related_name="goods_supplied") 

class Supplier(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    company = fields.CharField(max_length=255, null=True)
    email = fields.CharField(max_length=255, null=True)
    phone = fields.CharField(max_length=20, null=True)


product_pydantic = pydantic_model_creator(Products, name="Product")
product_pydanticIn = pydantic_model_creator(Products, name="ProductIn", exclude_readonly=True)

supplier_pydantic = pydantic_model_creator(Supplier, name="Supplier")
supplier_pydanticIn = pydantic_model_creator(Supplier, name="SupplierIn", exclude_readonly=True)