from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from starlette.responses import JSONResponse
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr, BaseModel
from typing import List
from tortoise.exceptions import DoesNotExist
from dotenv import dotenv_values
from fastapi.middleware.cors import CORSMiddleware
from models import (
    supplier_pydantic,
    supplier_pydanticIn,
    Supplier,
    product_pydantic,
    product_pydanticIn,
    Products
)

app = FastAPI()
# Middleware для обработки CORS запросов
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Можешь указать конкретный адрес фронтенда вместо "*"
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],  # Разрешаем любые заголовки
)

@app.get('/')
def index():
    return {"msg": "Hello, World!"}

# -------------------- SUPPLIERS --------------------

@app.post('/supplier')
async def add_supplier(supplier_info: supplier_pydanticIn):
    supplier_obj = await Supplier.create(**supplier_info.dict(exclude_unset=True))
    response = await supplier_pydantic.from_tortoise_orm(supplier_obj)
    return {"status": "success", "data": response}

@app.get('/supplier')
async def get_all_suppliers():
    response = await supplier_pydantic.from_queryset(Supplier.all())
    return {"status": "success", "data": response}

@app.get('/supplier/{supplier_id}')
async def get_specific_supplier(supplier_id: int):
    try:
        response = await supplier_pydantic.from_queryset_single(
            Supplier.get(id=supplier_id)
        )
        return {"status": "success", "data": response}
    except DoesNotExist:
        return {"status": "error", "message": "Supplier not found"}

@app.put('/supplier/{supplier_id}')
async def update_supplier(supplier_id: int, supplier_info: supplier_pydanticIn):
    try:
        supplier_obj = await Supplier.get(id=supplier_id)
    except DoesNotExist:
        return {"status": "error", "message": "Supplier not found"}

    supplier_obj.name = supplier_info.name
    supplier_obj.company = supplier_info.company
    supplier_obj.email = supplier_info.email
    supplier_obj.phone = supplier_info.phone
    await supplier_obj.save()

    response = await supplier_pydantic.from_tortoise_orm(supplier_obj)
    return {"status": "success", "data": response}

@app.delete('/supplier/{supplier_id}')
async def delete_supplier(supplier_id: int):
    try:
        supplier_obj = await Supplier.get(id=supplier_id)
        await supplier_obj.delete()
        return {"status": "success", "message": "Supplier deleted successfully"}
    except DoesNotExist:
        return {"status": "error", "message": "Supplier not found"}

# -------------------- PRODUCTS --------------------

@app.post('/product/{supplier_id}')
async def add_product(supplier_id: int, product_info: product_pydanticIn):
    try:
        supplier = await Supplier.get(id=supplier_id)
    except DoesNotExist:
        return {"status": "error", "message": "Supplier not found"}

    product_data = product_info.dict(exclude_unset=True)

    product_data["revenue"] = product_data.get("revenue", 0) + \
                              product_data["unit_price"] * product_data.get("quantity_soft", 0)

    product_obj = await Products.create(supplied_by=supplier, **product_data)
    response = await product_pydantic.from_tortoise_orm(product_obj)
    return {"status": "success", "data": response}

@app.get('/product')
async def get_all_products():
    response = await product_pydantic.from_queryset(Products.all())
    return {"status": "success", "data": response}

@app.get('/product/{product_id}')
async def get_specific_product(product_id: int):
    try:
        response = await product_pydantic.from_queryset_single(
            Products.get(id=product_id)
        )
        return {"status": "success", "data": response}
    except DoesNotExist:
        return {"status": "error", "message": "Product not found"}

@app.put('/product/{product_id}')
async def update_product(product_id: int, product_info: product_pydanticIn):
    try:
        product_obj = await Products.get(id=product_id)
    except DoesNotExist:
        return {"status": "error", "message": "Product not found"}

    product_obj.name = product_info.name
    product_obj.quantity_in_stock = product_info.quantity_in_stock
    product_obj.quantity_soft = product_info.quantity_soft
    product_obj.unit_price = product_info.unit_price
    product_obj.revenue = product_info.revenue
    await product_obj.save()

    response = await product_pydantic.from_tortoise_orm(product_obj)
    return {"status": "success", "data": response}

@app.delete('/product/{product_id}')
async def delete_product(product_id: int):
    try:
        product_obj = await Products.get(id=product_id)
        await product_obj.delete()
        return {"status": "success", "message": "Product deleted successfully"}
    except DoesNotExist:
        return {"status": "error", "message": "Product not found"}

# -------------------- E-MAIL --------------------

class EmailSchema(BaseModel):
    email: List[EmailStr]

class EmailContent(BaseModel):
    message: str
    subject: str
    
# Load environment variables
credentials = dotenv_values(".env")

conf = ConnectionConfig(
    MAIL_USERNAME=credentials.get('EMAIL'),
    MAIL_PASSWORD=credentials.get('PASSWORD'),
    MAIL_FROM=credentials.get('EMAIL'),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME="Desired Name",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

@app.post("/email/{product}")
async def send_email(product: int, email_content: EmailContent):
    try:
        product_obj = await Products.get(id=product)
        supplier = await product_obj.supplied_by
    except DoesNotExist:
        return {"status": "error", "message": "Product or supplier not found"}

    supplier_email = supplier.email
    
    html = f"""
    <p>Hi, this is a test mail for product ID {product_obj.id}. Thanks for using FastAPI-Mail</p>
    <p>Message: {email_content.message}</p>
    """
    
    message = MessageSchema(
        subject=email_content.subject,
        recipients=[supplier_email],  # Must be a list
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    return {'status': 'success', 'message': 'Email sent successfully'}

# -------------------- DB CONFIG --------------------

register_tortoise(
    app,
    db_url='sqlite://db.sqlite3',
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True
)
