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
from sqlalchemy.exc import SQLAlchemyError
from typing import Any, List, Optional, Dict, Tuple

from database.session import get_async_session
from database.models import Products, Reviews, Colors, Forms, Category, preCategory

from config.config import settings

from .schemas import (
    ProductSchema,
    Reviews_schemas,
    Color_schemas,
    Form_schemas,
    Category_schemas,
    PreCategorySchema,
    
    Form_schemas_patch,
)
from .utils import save_img, random_id, get_static_img_url

router = APIRouter(prefix="/api", tags=["api"])


#
# =====get запросы=====
#
@router.get(
    "/products",
    summary="Получение всех продуктов",
    description="Получает товары, их цвета и формы из таблиц Products, Colors, Forms.",
    status_code=200,
)
async def get_products(session: AsyncSession = Depends(get_async_session)):

    try:
        async with session.begin():
            products_result = (
                await session.execute(
                    select(
                        Products.id,
                        Products.ru_name_name,
                        Products.ru_name_desc,
                        Products.en_name_name,
                        Products.en_name_desc,
                        Products.images,
                        Products.isFrom,
                        Products.preCategory_address,
                        Products.preCategory_ru_name,
                        Products.preCategory_en_name,
                        Products.price,
                        Products.options_isForm,
                        Products.options_isColor,
                        Products.options_formId,
                        Products.options_colorId,
                    )._set_entities(
                        Products.id,
                        Products.ru_name_name,
                        Products.ru_name_desc,
                        Products.en_name_name,
                        Products.en_name_desc,
                        Products.images,
                        Products.isFrom,
                        Products.preCategory_address,
                        Products.preCategory_ru_name,
                        Products.preCategory_en_name,
                        Products.price,
                        Products.options_isForm,
                        Products.options_isColor,
                        Products.options_formId,
                        Products.options_colorId,
                    )
                ),
            )
            color_result =   await session.execute(select(Colors.id, Colors.ru_name, Colors.en_name, Colors.rgb)),

            form_result =  await session.execute(select(
                    Forms.id, Forms.ru_name, Forms.en_name, Forms.changeForm, Forms.image
                )),

            color_data = {
                    row[0]: {"id": row[0], "ru_name": row[1], "en_name": row[2], "rgb": row[3]}
                    for row in color_result
                }
            form_data = {
                    row[0]: {
                        "id": row[0],
                        "ru_name": row[1],
                        "en_name": row[2],
                        "changeForm": row[3],
                        "image": await get_static_img_url(row[4]),
                    }
                    for row in form_result
                }
            products = []
            for row in products_result:
                form_ids = [int(id_) for id_ in row[13]] if row[13] else []
                color_ids = [int(id_) for id_ in row[14]] if row[14] else []
                form_data_ = []
                for id_ in form_ids:
                    try:
                        form_data_.append(form_data[id_])
                    except KeyError:
                        continue
                color_data_ = []
                for id_ in color_ids:
                    try:
                        color_data_.append(color_data[id_])
                    except KeyError:
                        continue
                product = {
                        "id": row[0],
                        "ru_name": {"name": row[1], "desc": row[2]},
                        "en_name": {"name": row[3], "desc": row[4]},
                        "images": [await get_static_img_url(img) for img in row[5]],
                        "isFrom": row[6],
                        "preCategory": {
                            "address": row[7],
                            "ru_name": row[8],
                            "en_name": row[9],
                        },
                        "price": row[10],
                        "options": {
                            "isForm": row[11],
                            "isColor": row[12],
                            "form": form_data_,
                            "color": color_data_,
                        },
                    }
                products.append(product)
            if not products:
                raise HTTPException(status_code=404, detail="Products not found")
            return {"Products": products}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

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
                preCategory.id,
                preCategory.ru_name,
                preCategory.en_name,
                preCategory.address,
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
                preCategory.id, preCategory.ru_name, preCategory.en_name, preCategory.address
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
    async with session:
        try:
            insert_data = []
            for product in products:
                product_id = random_id(100)
                ru_name = product.ru_name
                en_name = product.en_name
                images = product.images
                isFrom = product.isFrom
                preCategory = product.preCategory
                preCategory_address = preCategory.address
                preCategory_ru_name = preCategory.ru_name
                preCategory_en_name = preCategory.en_name
                price = product.price
                options = product.options
                options_isForm = options.isForm
                options_isColor = options.isColor
                options_form = options.form_ids
                options_color = options.color_ids

                imgs_paths = []
                imgs_paths_url = []
                for i, img_data in enumerate(images):
                    img_path = rf"{settings.STATIC_FOLDER}/img/{product_id}_{i}_product.png"
                    img_path_url = rf"static/img/{product_id}_{i}_product.png"
                    await save_img(img_data, img_path)
                    imgs_paths.append(img_path)
                    imgs_paths_url.append(img_path_url)

                insert_data.append(
                    {
                        "id": product_id,
                        "ru_name_name": ru_name.name,
                        "ru_name_desc": ru_name.desc,
                        "en_name_name": en_name.name,
                        "en_name_desc": en_name.desc,
                        "images": imgs_paths_url,
                        "isFrom": isFrom,
                        "preCategory_address": preCategory_address,
                        "preCategory_ru_name": preCategory_ru_name,
                        "preCategory_en_name": preCategory_en_name,
                        "price": price,
                        "options_isForm": options_isForm,
                        "options_isColor": options_isColor,
                        "options_formId": options_form,
                        "options_colorId": options_color,
                    }
                )

            stmt = insert(Products).values(insert_data)
            await session.execute(stmt)
            await session.commit()
            return {"message": "Products created successfully"}
        except Exception as e:
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
            stmt = insert(preCategory).values(insert_data)
            await session.execute(stmt)
            await session.commit()
            return {"message": "Pre-categories created successfully"}
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
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
            stmt = delete(preCategory).where(preCategory.id.in_(precategory_ids))
            await session.execute(stmt)
            await session.commit()
            return {"message": "preCategories deleted successfully"}
        except Exception as e:
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
    async with session:
        try:
            # Get the existing product
            existing_product = await session.get(Products, product_id)
            if not existing_product:
                raise HTTPException(status_code=404, detail="Product not found")

            # Update the product details
            existing_product.ru_name_name = product.ru_name.name
            existing_product.ru_name_desc = product.ru_name.desc
            existing_product.en_name_name = product.en_name.name
            existing_product.en_name_desc = product.en_name.desc
            existing_product.isFrom = product.isFrom
            existing_product.preCategory_address = product.preCategory.address
            existing_product.preCategory_ru_name = product.preCategory.ru_name
            existing_product.preCategory_en_name = product.preCategory.en_name
            existing_product.price = product.price
            existing_product.options_isForm = product.options.isForm
            existing_product.options_isColor = product.options.isColor
            existing_product.options_formId = product.options.form_ids
            existing_product.options_colorId = product.options.color_ids
            images = product.images

            # Update or add new images
            if images:
                for i, img in enumerate(images):
                    img_path = (
                        rf"{settings.STATIC_FOLDER}/img/{product_id}_{i}_product.png"
                    )
                    img_path_url = rf"static/img/{product_id}_{i}_product.png"
                    await save_img(await img.read(), img_path)
                    existing_product.images.append(img_path_url)

            await session.commit()
            return {"message": "Product updated successfully"}

        except Exception as e:
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
            stmt = update(preCategory).where(preCategory.id == precategory_id).values(
                update_data
            )
            await session.execute(stmt)
            await session.commit()
            return {"message": "Pre-category updated successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
