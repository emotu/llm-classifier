"""
models.py

@author: Emotu Balogun
@created: December 1, 2024

Database models for the FastAPI application using SQLModel and SQLAlchemy.

SQLModel-based models that serve as both database tables and Pydantic models
for FastAPI request/response validation.

Key Features:
    - SQLModel integration for type-safe database models
    - SQLAlchemy foundation for robust database operations
    - Pydantic model validation built-in
    - FastAPI compatibility for automatic API documentation

Note:
    All models should inherit from SQLModel and define table=True for database tables
    or table=False for Pydantic-only models.

Example:
    >>> from sqlmodel import SQLModel, Field
    >>>
    >>> class User(SQLModel, table=True):
    ...     id: int = Field(default=None, primary_key=True)
    ...     username: str = Field(index=True)
    ...     email: str = Field(unique=True)

:module: app.models
:requires: sqlmodel, sqlalchemy
"""

import re
import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, computed_field, field_serializer
from pydantic_extra_types.country import CountryAlpha2
from sqlalchemy import Column, DateTime, String, event, func
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.ext.declarative import declared_attr
from sqlmodel import Field, Relationship, SQLModel

from app.config import settings


class TimestampMixin:
    @declared_attr
    def date_created(cls):
        return Column(DateTime, default=func.now(), nullable=False)

    @declared_attr
    def last_updated(cls):
        return Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class Industry(SQLModel, table=True):
    # Override ID, converting it to a slugified string
    id: str = Field(primary_key=True)
    name: str


class Address(BaseModel):
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    state: str | None = None
    postcode: str | None = None
    country: CountryAlpha2 | None = None

    def __repr__(self):
        return str(self.model_dump())

    # Custom serialization logic
    @field_serializer("*")
    def serialize_address(self, value: Any, field_name: str) -> Any:
        return value  # Pass-through for primitive types; no extra serialization needed

    # Optional: Add a method to convert the object to a dictionary
    def to_dict(self):
        return self.model_dump()


class Company(TimestampMixin, SQLModel, table=True):
    model_config = ConfigDict(str_strip_whitespace=True)  # type: ignore
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    website: str | None = Field(default=None, sa_type=String)
    description: str | None = None

    industries: list[str] | None = Field(
        default=[], sa_column=Column(ARRAY(String), nullable=True)
    )

    country: CountryAlpha2 | None = Field(default=None)
    address: dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))

    principal_person: str | None = None
    principal_designation: str | None = None

    business_objectives: str | None = None
    number_of_employees: str | None = None

    contact_name: str | None = None
    contact_email: EmailStr | None = Field(default=None, sa_type=String)
    scopes: list[str] | None = Field(sa_column=Column(ARRAY(String), nullable=True))

    documents: list["Document"] = Relationship(back_populates="company")


class Document(TimestampMixin, SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    description: str | None = None
    mime_type: str | None = None
    source: Literal["uploaded", "generated"] | None = Field(
        default=None, sa_type=String
    )

    content: str | None = None
    filename: str | None = None
    status: Literal["pending", "completed"] | None = Field(default=None, sa_type=String)

    company_id: uuid.UUID = Field(foreign_key="company.id", ondelete="CASCADE")
    company: Company = Relationship(back_populates="documents")

    download_url: str | None = Field(default=None)

    @computed_field
    @property
    def document_url(self) -> str:
        return f"{settings.BASE_URL}/downloads/documents/{self.id}"


class NaceActivity(BaseModel):
    activity: str
    subactivities: list[str] | None = []

    def __repr__(self):
        return str(self.model_dump())


class Scope(TimestampMixin, SQLModel, table=True):
    model_config = ConfigDict(str_strip_whitespace=True)  # type: ignore

    id: str = Field(default=None, primary_key=True)

    class_name: str = Field(default=None, index=True)
    class_code: str = Field(default=None, unique=True, index=True)
    class_description: str | None = None

    group_name: str = Field(default=None, index=True)
    group_code: str = Field(default=None, index=True)
    group_description: str | None = None

    division_name: str = Field(default=None, index=True)
    division_code: str = Field(default=None, index=True)
    division_description: str | None = None

    section_name: str = Field(default=None, index=True)
    section_code: str = Field(default=None, index=True)
    section_description: str | None = None

    included_activities: list[dict] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    excluded_activities: list[dict] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )

    # @computed_field
    # @property
    # def included_activities(self) -> list[NaceActivity]:
    #     return [
    #         NaceActivity.model_validate(activity)
    #         for activity in self.raw_included_activities
    #     ]

    # @included_activities.setter
    # def included_activities(self, value: list[NaceActivity] | None):
    #     if value is None:
    #         return
    #     self.raw_included_activities = [activity.model_dump() for activity in value]

    # @computed_field
    # @property
    # def excluded_activities(self) -> list[NaceActivity]:
    #     return [
    #         NaceActivity.model_validate(activity)
    #         for activity in self.raw_excluded_activities
    #     ]

    # @excluded_activities.setter
    # def excluded_activities(self, value: list[NaceActivity] | None):
    #     if value is None:
    #         return
    #     self.raw_excluded_activities = [activity.model_dump() for activity in value]

    @classmethod
    def remove_all_whitespace(cls, v):
        if isinstance(v, str):
            return re.sub(r"\s+", "", v)
        return v


@event.listens_for(Scope, "before_insert")
@event.listens_for(Scope, "before_update")
def before_insert(mapper, connection, target):
    target.id = target.class_code
