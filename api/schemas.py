from typing import Any, List, Optional, Dict
from pydantic import BaseModel
from typing import Union
from fastapi_users import schemas

class ProductNameSchema(BaseModel):
    name: str
    desc: str


class PreCategorySchema(BaseModel):
    address: str
    ru_name: str
    en_name: str


class OptionsSchema(BaseModel):
    isForm: bool
    isColor: bool
    form_ids: List[int]
    color_ids: List[int]

class PriceSchema(BaseModel):
    ru_name: float
    en_name: float
class ProductSchema(BaseModel):
    ru_name: ProductNameSchema
    en_name: ProductNameSchema
    images: List[str]
    isFrom: bool
    preCategory: List[PreCategorySchema]
    price: PriceSchema
    options: OptionsSchema


class lanNameSchemas(BaseModel):
    en_name: str
    ru_name: str


class Color_schemas(BaseModel):
    name: lanNameSchemas
    rgb: str


class Form_schemas(BaseModel):
    name: lanNameSchemas
    changeForm: float
    image: str


class Form_schemas_patch(BaseModel):
    name: lanNameSchemas
    changeForm: float

class Auth_schemas(BaseModel):
    login: str
    password: str


class Contents_schemas(BaseModel):
    Title: str
    Description: str

class Reviews_schemas(BaseModel):
    Contents: Contents_schemas
    Rate: int
    ProductId: int


class Category_schemas(BaseModel):
    ru_name: str
    en_name: str
    address: str
    preCategory: List[int]


class UserRead(schemas.BaseUser[int]):
    id: int
    email: str
    username: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False

    class Config:
        orm_mode = True


class UserCreate(schemas.BaseUserCreate):
    username: str
    email: str
    password: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False   

class MetatagsSchema(BaseModel):
    address: str
    title: str
    description: str
    keywords: str


class MetatagsSchemaPatch(BaseModel):
    title: str
    description: str
    keywords: str


class MetatagsSchemaPath(BaseModel):
    address: Union[str, bool]

class MetatagsResponse(BaseModel):
    metatags: List[MetatagsSchema]
