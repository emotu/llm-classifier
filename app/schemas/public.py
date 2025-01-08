import uuid
from typing import Any, Literal

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    EmailStr,
    field_serializer,
    field_validator,
)
from pydantic_extra_types.country import CountryAlpha2, CountryInfo, _countries

from app.models.assets import Address, Industry


class ScopeModel(BaseModel):
    id: str

    class_name: str
    class_code: str
    class_description: str | None = None

    group_name: str
    group_code: str
    group_description: str | None = None

    division_name: str
    division_code: str
    division_description: str | None = None

    section_name: str
    section_code: str
    section_description: str | None = None

    included_activities: list[dict] | None = None
    excluded_activities: list[dict] | None = None


class DependencyResponse(BaseModel):
    """
    # Response model for application dependencies endpoint

    This model defines the structure for returning all reference data and dependencies
    needed by client applications. It includes core data like country lists and
    industry classifications that are required for proper application functionality.

    ## Attributes
    - `countries` (`list[CountryInfo]`): List of supported countries with their metadata
    - `industries` (`list[Industry]`): List of available industry classifications

    ## Example
    ```json
    {
        "countries": [
            {"name": "United States", "code": "US", ...},
            {"name": "Canada", "code": "CA", ...}
        ],
        "industries": [
            {"id": "technology", "name": "Technology"},
            {"id": "healthcare", "name": "Healthcare"}
        ]
    }
    ```
    """

    countries: list[CountryInfo] = _countries()
    industries: list[Industry] | None = []
    scopes: list[ScopeModel] | None = []


class CrawlRequest(BaseModel):
    website: AnyHttpUrl

    @field_validator("website", mode="before")
    @classmethod
    def validate_website(cls, v):
        if isinstance(v, str):
            # Add https:// if no scheme is provided
            if not v.startswith(("http://", "https://")):
                v = f"https://{v}"
        return v

    @field_serializer("website")
    def serialize_website(self, value: AnyHttpUrl, _info: Any) -> str:
        return str(value)


class BusinessScope(BaseModel):
    code: str
    name: str
    description: str


class CompanyRequest(BaseModel):
    website: AnyHttpUrl | None = None
    name: str | None = None
    description: str | None = None
    industries: list[str] | None = None
    address: Address | None = None

    principal_person: str | None = None
    principal_designation: str | None = None

    objectives: str | None = None
    number_of_employees: str | None = None

    contact_name: str | None = None
    contact_email: EmailStr | None = None
    scopes: list[str] | None = None
    country: CountryAlpha2 | None = None

    @field_serializer("website")
    def serialize_website(self, value: AnyHttpUrl, _info: Any) -> str:
        return str(value)


class ActionStatus(BaseModel):
    status: Literal["success", "failed", "error"]
    code: str | None = None
    description: str | None = None
    payload: dict | None = dict


class DocumentResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    document_url: str | None = None
    mime_type: str | None = None
    source: str | None = None
    status: str | None = None
    filename: str | None = None
    company_id: uuid.UUID | None = None
