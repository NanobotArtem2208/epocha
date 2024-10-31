import uuid
from datetime import datetime
from typing import Union
from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    String,
    JSON,
    Boolean,
    Float,
    TIMESTAMP,
    BigInteger,
    DateTime,
    func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Column, String, Boolean, Integer, TIMESTAMP, ForeignKey 


# Генератор рандомного id
def random_id():
    return int(f"100{uuid.uuid4().int >> (128 - 32)}")


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())  # UTC
    updated: Mapped[DateTime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class Products(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, unique=True)
    ru_name_name: Mapped[str] = mapped_column(String(255))
    ru_name_desc: Mapped[str] = mapped_column(String(1024))
    en_name_name: Mapped[str] = mapped_column(String(255))
    en_name_desc: Mapped[str] = mapped_column(String(1024))
    images: Mapped[list[str]] = mapped_column(JSON)
    isFrom: Mapped[bool] = mapped_column(Boolean, default=False)
    preCategory_address: Mapped[str] = mapped_column(String(255))
    preCategory_ru_name: Mapped[str] = mapped_column(String(255))
    preCategory_en_name: Mapped[str] = mapped_column(String(255))
    price: Mapped[float] = mapped_column(Float, default=0.0)
    options_isForm: Mapped[bool] = mapped_column(Boolean, default=False)
    options_isColor: Mapped[bool] = mapped_column(Boolean, default=False)
    options_formId: Mapped[list[int]] = mapped_column(JSON)
    options_colorId: Mapped[list[int]] = mapped_column(JSON)


class Colors(Base):
    __tablename__ = "colors"
 
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    en_name: Mapped[str] = mapped_column(String(255))
    ru_name: Mapped[str] = mapped_column(String(255))
    rgb: Mapped[str] = mapped_column(String(128))


class Forms(Base):
    __tablename__ = "forms"
   
    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, unique=True
    )
    en_name: Mapped[str] = mapped_column(String(255))
    ru_name: Mapped[str] = mapped_column(String(255))
    changeForm: Mapped[float] = mapped_column(Float, default=0.0)
    image: Mapped[str] = mapped_column()


class Reviews(Base):
    __tablename__ = "reviews"
   
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    Title: Mapped[str] = mapped_column(String(255))
    Description: Mapped[str] = mapped_column(String(4096))
    Rate: Mapped[int] = mapped_column(Integer)
    ProductId: Mapped[int] = mapped_column(BigInteger, nullable=False)


class Category(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    address: Mapped[str] = mapped_column(String(255))
    ru_name: Mapped[str] = mapped_column(String(255))
    en_name: Mapped[str] = mapped_column(String(255))
    preCategory: Mapped[list[int]] = mapped_column(JSON)


class preCategory(Base):
    __tablename__ = "preCategory"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    address: Mapped[str] = mapped_column(String(255))
    ru_name: Mapped[str] = mapped_column(String(255))
    en_name: Mapped[str] = mapped_column(String(255))


class Metatags(Base):
    __tablename__ = "metatags"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    address: Mapped[str] = mapped_column(String(255), unique=True)
    title: Mapped[str] = mapped_column(String(60))
    description: Mapped[str] = mapped_column(String(160))
    keywords: Mapped[str] = mapped_column(String(1024))
