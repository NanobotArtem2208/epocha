import uuid
import asyncio

from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache
from fastapi_cache.backends.redis import RedisBackend

from fastapi import APIRouter, Depends, Body, HTTPException, File, UploadFile
from sqlalchemy import select, insert, update, text, delete, join
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_
from sqlalchemy import case
from sqlalchemy.sql.expression import null
from sqlalchemy.sql import bindparam
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import Any, List, Optional, Dict, Tuple

from database.session import get_async_session
from database.models import (
    Products,
    Reviews,
    Colors,
    Forms,
    Category,
    PreCategory,
    Metatags,
    PreCategoryProducts,
    product_precategory_association,
)

from config.config import settings

from .schemas import (
    ProductSchema,
    Reviews_schemas,
    Color_schemas,
    Form_schemas,
    Category_schemas,
    PreCategorySchema,
    Form_schemas_patch,
    MetatagsSchema,
    MetatagsSchemaPatch,
    MetatagsSchemaPath,
    MetatagsResponse,
)
from .utils import save_img, random_id, get_static_img_url

router = APIRouter(prefix="/api", tags=["api"])


@router.get(
    "/products",
    summary="Получение всех продуктов",
    description="Получает товары, их цвета, формы и предкатегории из таблиц Products, Colors, Forms, и PreCategoryProducts.",
    status_code=200,
)
async def get_products(session: AsyncSession = Depends(get_async_session)):
    async with session:
       
        products_stmt = select(
            Products.id,
            Products.ru_name_name,
            Products.ru_name_desc,
            Products.en_name_name,
            Products.en_name_desc,
            Products.images,
            Products.isFrom,
            Products.price_ru,
            Products.price_en,
            Products.options_isForm,
            Products.options_isColor,
            Products.options_formId,
            Products.options_colorId,
        )
        color_stmt = select(Colors.id, Colors.ru_name, Colors.en_name, Colors.rgb)
        form_stmt = select(
            Forms.id, Forms.ru_name, Forms.en_name, Forms.changeForm, Forms.image
        )


        precategory_stmt = select(
            PreCategoryProducts.id,
            PreCategoryProducts.address,
            PreCategoryProducts.ru_name,
            PreCategoryProducts.en_name,
            product_precategory_association.c.product_id,
        ).join(
            product_precategory_association,
            PreCategoryProducts.id == product_precategory_association.c.precategory_id,
        )


        products_result = await session.execute(products_stmt)
        color_result = await session.execute(color_stmt)
        form_result = await session.execute(form_stmt)
        precategory_result = await session.execute(precategory_stmt)


        color_data = {
            row.id: {
                "id": row.id,
                "ru_name": row.ru_name,
                "en_name": row.en_name,
                "rgb": row.rgb,
            }
            for row in color_result.scalars()
        }


        form_data = {
            row.id: {
                "id": row.id,
                "ru_name": row.ru_name,
                "en_name": row.en_name,
                "changeForm": row.changeForm,
                "image": await get_static_img_url(row.image),
            }
            for row in form_result.scalars()
        }

  
        precategory_data = {}
        for row in precategory_result:
            product_id = row.product_id
            if product_id not in precategory_data:
                precategory_data[product_id] = []
            precategory_data[product_id].append(
                {
                    "id": row.id,
                    "address": row.address,
                    "ru_name": row.ru_name,
                    "en_name": row.en_name,
                }
            )

 
        products = []
        for row in products_result.all():
            form_ids = (
                [int(id_) for id_ in row.options_formId] if row.options_formId else []
            )
            color_ids = (
                [int(id_) for id_ in row.options_colorId] if row.options_colorId else []
            )

            form_data_ = [form_data[id_] for id_ in form_ids if id_ in form_data]
            color_data_ = [color_data[id_] for id_ in color_ids if id_ in color_data]

            product = {
                "id": row.id,
                "ru_name": {"name": row.ru_name_name, "desc": row.ru_name_desc},
                "en_name": {"name": row.en_name_name, "desc": row.en_name_desc},
                "images": [await get_static_img_url(img) for img in row.images],
                "isFrom": row.isFrom,
                "price": {"ru_name": row.price_ru, "en_name": row.price_en},
                "options": {
                    "isForm": row.options_isForm,
                    "isColor": row.options_isColor,
                    "form": form_data_,
                    "color": color_data_,
                },
                "preCategory": precategory_data.get(
                    row.id, []
                ),  
            }
            products.append(product)

        if not products:
            raise HTTPException(status_code=404, detail="Products not found")

        return {"Products": products}

@router.get(
    "/products/{product_id}",
    summary="Получение продукта по ID",
    description="Получает товар, его цвета, формы и предкатегории из таблиц Products, Colors, Forms, и PreCategoryProducts по указанному ID.",
    status_code=200,
)
async def get_product_by_id(product_id: int, session: AsyncSession = Depends(get_async_session)):
    async with session:
 
        product_stmt = select(
            Products.id,
            Products.ru_name_name,
            Products.ru_name_desc,
            Products.en_name_name,
            Products.en_name_desc,
            Products.images,
            Products.isFrom,
            Products.price_ru,
            Products.price_en,
            Products.options_isForm,
            Products.options_isColor,
            Products.options_formId,
            Products.options_colorId,
        ).where(Products.id == product_id)

        color_stmt = select(Colors.id, Colors.ru_name, Colors.en_name, Colors.rgb)
        form_stmt = select(
            Forms.id, Forms.ru_name, Forms.en_name, Forms.changeForm, Forms.image
        )

      
        precategory_stmt = select(
            PreCategoryProducts.id,
            PreCategoryProducts.address,
            PreCategoryProducts.ru_name,
            PreCategoryProducts.en_name,
            product_precategory_association.c.product_id
        ).join(
            product_precategory_association,
            PreCategoryProducts.id == product_precategory_association.c.precategory_id
        ).where(product_precategory_association.c.product_id == product_id)

 
        product_result = await session.execute(product_stmt)
        color_result = await session.execute(color_stmt)
        form_result = await session.execute(form_stmt)
        precategory_result = await session.execute(precategory_stmt)

        product = product_result.first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

     
        color_data = {
            row.id: {
                "id": row.id,
                "ru_name": row.ru_name,
                "en_name": row.en_name,
                "rgb": row.rgb,
            }
            for row in color_result.scalars()
        }


        form_data = {
            row.id: {
                "id": row.id,
                "ru_name": row.ru_name,
                "en_name": row.en_name,
                "changeForm": row.changeForm,
                "image": await get_static_img_url(row.image),
            }
            for row in form_result.scalars()
        }

 
        precategory_data = [
            {
                "id": row.id,
                "address": row.address,
                "ru_name": row.ru_name,
                "en_name": row.en_name,
            }
            for row in precategory_result
        ]

        # Build product object
        form_ids = [int(id_) for id_ in product.options_formId] if product.options_formId else []
        color_ids = [int(id_) for id_ in product.options_colorId] if product.options_colorId else []

        form_data_ = [form_data[id_] for id_ in form_ids if id_ in form_data]
        color_data_ = [color_data[id_] for id_ in color_ids if id_ in color_data]

        product_obj = {
            "id": product.id,
            "ru_name": {"name": product.ru_name_name, "desc": product.ru_name_desc},
            "en_name": {"name": product.en_name_name, "desc": product.en_name_desc},
            "images": [await get_static_img_url(img) for img in product.images],
            "isFrom": product.isFrom,
            "price": {"ru_name": product.price_ru, "en_name": product.price_en},
            "options": {
                "isForm": product.options_isForm,
                "isColor": product.options_isColor,
                "form": form_data_,
                "color": color_data_,
            },
            "preCategory": precategory_data,  
        }

        return {"Product": product_obj}


@router.get(
    "/reviews",
    summary="Получение всех отзывов",
    description="Получает все отзывы из таблицы Reviews",
    status_code=200,
)
async def get_reviews(session: AsyncSession = Depends(get_async_session)):
    async with session:
        try:
            stmt = select(
                Reviews.id, Reviews.ProductId, Reviews.Title, Reviews.Description, Reviews.Rate
            )
            result = await session.execute(stmt)
            reviews = []
            for row in result.all():
                review = {
                    "id": row[0],
                    "Contents": {"Title": row[2], "Description": row[3]},
                    "Rate": row[4],
                    "ProductId": row[1],
                }
                reviews.append(review)

            return reviews
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/category",
    summary="Получение всех категорий",
    description="Получает все категории из таблицы Category",
    status_code=200,
)
async def get_category(session: AsyncSession = Depends(get_async_session)):
    async with session:
        try:
            category_stmt = select(
                Category.id, Category.ru_name, Category.en_name, Category.address, Category.preCategory
            )
            category_result = await session.execute(category_stmt)

            preCategory_stmt = select(
                PreCategory.id,
                PreCategory.ru_name,
                PreCategory.en_name,
                PreCategory.address,
            )
            preCategory_result = await session.execute(preCategory_stmt)

            preCategory_data = {
                row[0]: PreCategorySchema(
                    id=row[0], ru_name=row[1], en_name=row[2], address=row[3]
                )
                for row in preCategory_result.all()
            }

            result = category_result.all()
            categories = []
            for row in result:
                preCategories = [
                    preCategory_data[id] for id in row.preCategory if id in preCategory_data
                ]
                category = {
                    "id": row.id,
                    "ru_name": row.ru_name,
                    "en_name": row.en_name,
                    "address": row.address,
                    "preCategory": preCategories,
                }
                categories.append(category)

            return categories
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/preCategory",
    summary="Получение всех пред категорий",
    description="Получает все пред категории из таблицы preCategory",
    status_code=200,
)
async def get_preCategory(session: AsyncSession = Depends(get_async_session)):
    async with session:
        try: 
            stmt = select(
                PreCategory.id, PreCategory.ru_name, PreCategory.en_name, PreCategory.address
            )
            result = await session.execute(stmt)
            preCategories = []
            for row in result.all():
                preCategory_form = {
                    "id": row[0],
                    "ru_name": row[1],
                    "en_name": row[2],
                    "address": row[3],
                }
                preCategories.append(preCategory_form)

            return {"preCategories": preCategories}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/colors",
    summary="Получение всех цветов",
    description="Получает все цвета из таблицы Colors",
    status_code=200,
)
async def get_colors(session: AsyncSession = Depends(get_async_session)):
    async with session:
        try:
            stmt = select(Colors.id, Colors.ru_name, Colors.en_name, Colors.rgb)
            result = await session.execute(stmt)
            colors = []
            for row in result.all():
                color = {
                    "id": row[0],
                    "ru_name": row[1],
                    "en_name": row[2],
                    "rgb": row[3],
                }
                colors.append(color)

            return {"colors": colors}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/forms",
    summary="Получение всех форм",
    description="Получает все формы из таблицы Forms",
    status_code=200,
)
async def get_forms(session: AsyncSession = Depends(get_async_session)):
    async with session:
        try:
            stmt = select(Forms.id, Forms.ru_name, Forms.en_name, Forms.changeForm, Forms.image)
            result = await session.execute(stmt)
            forms = []
            for row in result.all():
                form = {
                    "id": row[0],
                    "ru_name": row[1],
                    "en_name": row[2],
                    "changeForm": row[3],
                    "image": await get_static_img_url(row[4]),
                }
                forms.append(form)

            return {"forms": forms}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


#
# =====post запросы=====
#


@router.post(
    "/products",
    summary="Создание продуктов",
    description="Создает новые продукты, сохраняя данные в таблицу products и фото в папку static/img",
    status_code=201,
)
async def create_products(
    products: List[ProductSchema] = Body(...),
    session: AsyncSession = Depends(get_async_session),
):
    async with session.begin():
        try:
            insert_data = []
            for product in products:
                product_id = random_id(100)
                ru_name = product.ru_name
                en_name = product.en_name
                images = product.images
                isFrom = product.isFrom
                preCategory = product.preCategory
                price_ru = product.price.ru_name
                price_en = product.price.en_name
                options = product.options
                options_isForm = options.isForm
                options_isColor = options.isColor
                options_form_ids = options.form_ids
                options_color_ids = options.color_ids

                # Сохранение изображений
                imgs_paths_url = []
                for i, img_data in enumerate(images):
                    img_path = (
                        rf"{settings.STATIC_FOLDER}/img/{product_id}_{i}_product.png"
                    )
                    img_path_url = rf"static/img/{product_id}_{i}_product.png"
                    await save_img(img_data, img_path)
                    imgs_paths_url.append(img_path_url)

                # Сохранение предкатегорий
                pre_category_ids = []
                for category in preCategory:
                    # Проверяем, существует ли предкатегория
                    existing_category = await session.execute(
                        select(PreCategoryProducts).where(
                            PreCategoryProducts.ru_name == category.ru_name,
                            PreCategoryProducts.en_name == category.en_name,
                            PreCategoryProducts.address == category.address,
                        )
                    )
                    existing_category = existing_category.scalars().first()

                    if existing_category:
                        pre_category_ids.append(existing_category.id)
                    else:
                        # Создаем новую предкатегорию
                        new_category = PreCategoryProducts(
                            address=category.address,
                            ru_name=category.ru_name,
                            en_name=category.en_name,
                        )
                        session.add(new_category)
                        await session.flush()  # Сохраняем, чтобы получить ID
                        pre_category_ids.append(new_category.id)

                # Формирование данных для вставки
                insert_data.append(
                    {
                        "id": product_id,
                        "ru_name_name": ru_name.name,
                        "ru_name_desc": ru_name.desc,
                        "en_name_name": en_name.name,
                        "en_name_desc": en_name.desc,
                        "images": imgs_paths_url,
                        "isFrom": isFrom,
                        "price_ru": price_ru,
                        "price_en": price_en,
                        "options_isForm": options_isForm,
                        "options_isColor": options_isColor,
                        "options_formId": options_form_ids,
                        "options_colorId": options_color_ids,
                    }
                )

            # Вставка данных в таблицу Products
            stmt = insert(Products).values(insert_data)
            await session.execute(stmt)

            # Связываем продукты с предкатегориями
            for product_id in [data["id"] for data in insert_data]:
                for category_id in pre_category_ids:
                    stmt = insert(product_precategory_association).values(
                        product_id=product_id, precategory_id=category_id
                    )
                    await session.execute(stmt)

            await session.commit()
            return {"message": "Products created successfully"}
        except Exception as e:
            await session.rollback()  # Откат транзакции в случае ошибки
            raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/reviews",
    summary="Создание отзывов",
    description="Создает отзыв сохраняя данные в таблице Reviews",
    status_code=201,
)
async def create_review(
    review: Reviews_schemas = Body(...),
    session: AsyncSession = Depends(get_async_session),
):
    async with session:
        contents = review.Contents
        title = contents.Title
        description = contents.Description
        rate = review.Rate
        productId = review.ProductId
        try:
            stmt = insert(Reviews).values(
                id=random_id(101),
                Title=title,
                Description=description,
                Rate=rate,
                ProductId=productId,
            )
            await session.execute(stmt)
            await session.commit()
            return {"message": "Review created successfully"}

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/colors",
    summary="Создание цветов",
    description="Создает новые цвета",
    status_code=201,
)
async def create_colors(
    colors: List[Color_schemas] = Body(...),
    session: AsyncSession = Depends(get_async_session),
):
    async with session:
        try:
            color_data = [
                {
                    "id": random_id(102),
                    "en_name": color.name.en_name,
                    "ru_name": color.name.ru_name,
                    "rgb": color.rgb,
                }
                for color in colors
            ]
            stmt = insert(Colors)
            await session.execute(stmt.values(color_data))
            await session.commit()
            return {"message": "Review created successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/forms",
    summary="Создание форм",
    description="Создает новые формы, сохраняя данные в таблице Forms",
    status_code=201,
)
async def create_forms(
    forms: List[Form_schemas] = Body(...),
    session: AsyncSession = Depends(get_async_session),
):
    async with session:
        try:
            form_data = []
            for form in forms:
                form_id = random_id(103)
                img_path = rf"{settings.STATIC_FOLDER}/img/{form_id}_form.png"
                img_path_url = rf"static/img/{form_id}_form.png"
                await save_img(form.image, img_path)
                form_data.append(
                    {
                        "id": form_id,
                        "en_name": form.name.en_name,
                        "ru_name": form.name.ru_name,
                        "changeForm": form.changeForm,
                        "image": img_path_url,
                    }
                )
            stmt = insert(Forms)
            result = await session.execute(stmt.values(form_data))
            await session.commit()
            return {"message": "Review created successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/categories",
    summary="Создание категорий",
    description="Создает категории, сохраняя данные в таблице Category",
    status_code=201,
)
async def create_categories(
    categories: List[Category_schemas] = Body(...),
    session: AsyncSession = Depends(get_async_session),
):
    async with session:
        try:
            category_data = [
                {
                    "id": random_id(104),
                    "en_name": category.en_name,
                    "ru_name": category.ru_name,
                    "address": category.address,
                    "preCategory": category.preCategory,
                }
                for category in categories
            ]
            stmt = insert(Category)
            await session.execute(stmt.values(category_data))
            await session.commit()
            return {"message": "Categories created successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/preCategories",
    summary="Создание пред категорий",
    description="Создает пред категории, сохраняя данные в таблице preCategory",
    status_code=201,
)
async def create_preCategories(
    precategories: List[PreCategorySchema] = Body(...),
    session: AsyncSession = Depends(get_async_session),
):
    async with session:
        try:
            insert_data = [
                {
                    "id": random_id(105),
                    "en_name": pre_category.en_name,
                    "ru_name": pre_category.ru_name,
                    "address": pre_category.address,
                }
                for pre_category in precategories
            ]
            stmt = insert(PreCategory).values(insert_data)
            await session.execute(stmt)
            await session.commit()
            return {"message": "Pre-categories created successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/metatags",
    summary="Создание метатегов",
    description="Создает метатеги, сохраняя данные в таблице Metatags",
    status_code=201,
)
async def create_metatags(
    metatags: List[MetatagsSchema] = Body(...),
    session: AsyncSession = Depends(get_async_session),
):
    async with session:
        try:
            for metatag in metatags:
                existing_metatag = await session.execute(
                    select(Metatags).where(Metatags.address == metatag.address)
                )
                if existing_metatag.scalars().first() is not None:
                    raise HTTPException(status_code=400, detail=f"Metatag with address {metatag.address} already exists")

            metatag_data = [
                {
                    "id": random_id(106),
                    "address": metatag.address,
                    "title": metatag.title,
                    "description": metatag.description,
                    "keywords": metatag.keywords,
                }
                for metatag in metatags
            ]

            stmt = insert(Metatags)
            await session.execute(stmt.values(metatag_data))
            await session.commit()
            return {"message": "Metatags created successfully"}
        except IntegrityError:
            await session.rollback()
            raise HTTPException(status_code=400, detail="Integrity constraint error")
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/getmetategs",
    summary="Получение метатегов",
    description="Получает метатеги по их адресу.\n Если `address` установлен в `True`, будут возвращены все метатеги. Если `address` установлен в `False`, будет возвращен пустой список.",
    status_code=201,
    response_model=MetatagsResponse,
)
async def get_metatags(
    metatags: MetatagsSchemaPath = Body(...),
    session: AsyncSession = Depends(get_async_session),
):
    async with session:
        try:
            if metatags.address is True:
                stmt = select(
                    Metatags.address,
                    Metatags.title,
                    Metatags.description,
                    Metatags.keywords,
                )
                result = await session.execute(stmt)
                metatags = result.all()
                return {"metatags": metatags}
            
            if metatags.address is False:
                return {"metatags": []}    
            
            else:
                stmt = select(Metatags.address, Metatags.title, Metatags.description, Metatags.keywords).where(Metatags.address == metatags.address)
                result = await session.execute(stmt)
                metatags = result.all()
                return {"metatags": metatags}
            
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=str(e))

#
# =====delete запросы=====
#
@router.delete(
    "/products",
    summary="Удаление продуктов",
    description="Удаляет продукты из таблицы Products по их id",
    status_code=200,
)
async def delete_products(
    product_ids: List[int] = Body(...),
    session: AsyncSession = Depends(get_async_session),
):
    async with session:
        try:
            stmt = delete(Products).where(Products.id.in_(product_ids))
            await session.execute(stmt)
            await session.commit()
            return {"message": "Products deleted successfully"}
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.delete(
    "/reviews",
    summary="Удаление отзывов",
    description="Удаляет отзывы из таблицы Reviews по их id",
    status_code=200,
)
async def delete_reviews(
    review_ids: List[int] = Body(...),
    session: AsyncSession = Depends(get_async_session),
):
    async with session:
        try:
            stmt = delete(Reviews).where(Reviews.id.in_(review_ids))
            await session.execute(stmt)
            await session.commit()
            return {"message": "Reviews deleted successfully"}
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.delete(
    "/colors",
    summary="Удаление цветов",
    description="Удаляет цвета из таблицы Colors по их id",
    status_code=200,
)
async def delete_colors(
    color_ids: List[int] = Body(...),
    session: AsyncSession = Depends(get_async_session),
):
    async with session:
        try:
            stmt = delete(Colors).where(Colors.id.in_(color_ids))
            await session.execute(stmt)
            await session.commit()
            return {"message": "Colors deleted successfully"}
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.delete(
    "/forms",
    summary="Удаление форм",
    description="Удаляет формы из таблицы Forms по их id",
    status_code=200,
)
async def delete_forms(
    form_ids: List[int] = Body(...),
    session: AsyncSession = Depends(get_async_session),
):
    async with session:
        try:
            stmt = delete(Forms).where(Forms.id.in_(form_ids))
            await session.execute(stmt)
            await session.commit()
            return {"message": "Forms deleted successfully"}
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.delete(
    "/categories",
    summary="Удаление категорий",
    description="Удаляет категории из таблицы Category по их id",
    status_code=200,
)
async def delete_categories(
    category_ids: List[int] = Body(...),
    session: AsyncSession = Depends(get_async_session),
):
    async with session:
        try:
            stmt = delete(Category).where(Category.id.in_(category_ids))
            await session.execute(stmt)
            await session.commit()
            return {"message": "Categories deleted successfully"}
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.delete(
    "/precategories",
    summary="Удаление пред категорий",
    description="Удаляет пред категории из таблицы preCategory по их id",
    status_code=200,
)
async def delete_precategories(
    precategory_ids: List[int] = Body(...),
    session: AsyncSession = Depends(get_async_session),
):
    async with session:
        try:
            stmt = delete(PreCategory).where(PreCategory.id.in_(precategory_ids))
            await session.execute(stmt)
            await session.commit()
            return {"message": "preCategories deleted successfully"}
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.delete(
    "/metatags",
    summary="Удаление метатегов",
    description="Удаляет метатеги из таблицы Metatags по их адресу",
    status_code=200,
)
async def delete_metatags(
    metatag: MetatagsSchemaPath = Body(...),
    session: AsyncSession = Depends(get_async_session),
):
    async with session:
        try:
            existing_metatag = await session.execute(
                select(Metatags).where(Metatags.address == metatag.address)
            )
            if existing_metatag.scalars().first() is None:
                raise HTTPException(status_code=404, detail=f"Metatag with address {metatag.address} not found")

            stmt = delete(Metatags).where(Metatags.address == metatag.address)
            await session.execute(stmt)
            await session.commit()
            return {"message": "Metatags deleted successfully"}
        except SQLAlchemyError as e:
            await session.rollback() 
            raise HTTPException(status_code=500, detail=str(e))

# PUT — полная замена объекта на обновленную версию
# PATCH — частичное изменение объекта


#
# =====patch запросы=====
#


@router.patch(
    "/products/{product_id}",
    summary="Update product",
    description="Update a product in the Products table by its id",
    status_code=200,
)
async def update_products(
    product_id: int,
    product: ProductSchema = Body(...),
    session: AsyncSession = Depends(get_async_session),
):
    async with session.begin():  # Используем async with для управления сессией
        try:
            # Получаем существующий продукт
            existing_product = await session.get(Products, product_id)
            if not existing_product:
                raise HTTPException(status_code=404, detail="Product not found")

            # Обновляем детали продукта
            existing_product.ru_name_name = product.ru_name.name
            existing_product.ru_name_desc = product.ru_name.desc
            existing_product.en_name_name = product.en_name.name
            existing_product.en_name_desc = product.en_name.desc
            existing_product.isFrom = product.isFrom

            # Обработка preCategory
            if product.preCategory:
                # Предполагается, что вы хотите обновить только первый элемент
                existing_product.preCategory.address = product.preCategory.address
                existing_product.preCategory.ru_name = product.preCategory.ru_name
                existing_product.preCategory.en_name = product.preCategory.en_name

            existing_product.price_ru = product.price.ru_name
            existing_product.price_en = product.price.en_name
            existing_product.options_isForm = product.options.isForm
            existing_product.options_isColor = product.options.isColor
            existing_product.options_formId = product.options.form_ids
            existing_product.options_colorId = product.options.color_ids

            images = product.images

            # Обновление или добавление новых изображений
            if images:
                existing_product.images.clear()  # Очистка существующих изображений
                for i, img in enumerate(images):
                    img_path = (
                        rf"{settings.STATIC_FOLDER}/img/{product_id}_{i}_product.png"
                    )
                    img_path_url = rf"static/img/{product_id}_{i}_product.png"
                    await save_img(await img.read(), img_path)  # Сохраняем изображение
                    existing_product.images.append(
                        img_path_url
                    )  # Добавляем путь к изображению

            await session.commit()  # Коммит изменений
            return {"message": "Product updated successfully"}

        except Exception as e:
            await session.rollback()  # Откат изменений в случае ошибки
            raise HTTPException(status_code=500, detail=str(e))

@router.patch(
    "/reviews/{review_id}",
    summary="Обновление отзывов",
    description="Обновляет отзывы в таблице Reviews по их id",
    status_code=200,
)
async def update_reviews(
    review_id: int,
    review: Reviews_schemas = Body(...),
    session: AsyncSession = Depends(get_async_session),
):
    async with session:
        try:
            update_data = {
                "Title": review.Contents.Title,
                "Description": review.Contents.Description,
                "Rate": review.Rate,
                "ProductId": review.ProductId,
            }
            stmt = update(Reviews).where(Reviews.id == review_id).values(update_data)
            await session.execute(stmt)
            await session.commit()
            return {"message": "Review updated successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.patch(
    "/colors/{color_id}",
    summary="Обновление цветов",
    description="Обновляет цвета в таблице Colors по их id",
    status_code=200,
)
async def update_colors(
    color_id: int,
    color: Color_schemas = Body(...),
    session: AsyncSession = Depends(get_async_session),
):
    async with session:
        try:
            update_data = {
                "en_name": color.name.en_name,
                "ru_name": color.name.ru_name,
                "rgb": color.rgb,
            }
            stmt = update(Colors).where(Colors.id == color_id).values(update_data)
            await session.execute(stmt)
            await session.commit()
            return {"message": "Color updated successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/forms/{form_id}",
    summary="Обновление форм",
    description="Обновляет формы в таблице Forms по их id",
    status_code=200,
)
async def update_forms(
    form_id: int,
    form: Form_schemas_patch = Body(...),
    session: AsyncSession = Depends(get_async_session),
):
    async with session:
        try:
            update_data = {
                "en_name": form.name.en_name,
                "ru_name": form.name.ru_name,
                "changeForm": form.changeForm,
            }
            stmt = update(Forms).where(Forms.id == form_id).values(update_data)
            await session.execute(stmt)
            await session.commit()
            return {"message": "Form updated successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.patch(
    "/categories/{category_id}",
    summary="Обновление категорий",
    description="Обновляет категории в таблице Category по их id",
    status_code=200,
)
async def update_categories(
    category_id: int,
    category: Category_schemas = Body(...),
    session: AsyncSession = Depends(get_async_session),
):
    async with session:
        try:
            update_data = {
                "en_name": category.en_name,
                "ru_name": category.ru_name,
                "address": category.address,
                "preCategory": category.preCategory,
            }
            stmt = update(Category).where(Category.id == category_id).values(update_data)
            await session.execute(stmt)
            await session.commit()
            return {"message": "Category updated successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/precategories/{precategory_id}",
    summary="Обновление пред категорий",
    description="Обновляет пред категории в таблице preCategory по их id",
    status_code=200,
)
async def update_precategories(
    precategory_id: int,
    precategory: PreCategorySchema = Body(...),
    session: AsyncSession = Depends(get_async_session),
):
    async with session:
        try:
            update_data = {
                "en_name": precategory.en_name,
                "ru_name": precategory.ru_name,
                "address": precategory.address,
            }
            stmt = update(PreCategory).where(PreCategory.id == precategory_id).values(
                update_data
            )
            await session.execute(stmt)
            await session.commit()
            return {"message": "Pre-category updated successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/metatags/{metatag_address}",
    summary="Обновление метатегов",
    description="Обновляет метатеги в таблице Metatags по их id",
    status_code=200,
)
async def update_metatags(
    metatag_address: str,
    metatag: MetatagsSchemaPatch = Body(...),
    session: AsyncSession = Depends(get_async_session),
):

    async with session:
        try:
            update_data = {
                "title": metatag.title,
                "description": metatag.description,
                "keywords": metatag.keywords,
            }
            stmt = update(Metatags).where(Metatags.address == metatag_address).values(update_data)
            await session.execute(stmt)
            await session.commit()
            return {"message": "Metatag updated successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
