"""
public.py

Public API router for unauthenticated endpoints.

Provides FastAPI router definitions for public endpoints that do not require authentication.
Handles public data access and services.

:module: app.routers.public
:requires: fastapi
"""

from http import HTTPStatus

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.llm.classifier import Classifier, create_classifier_dependency
from app.models import get_session
from app.schemas.public import (
    CompanyRequest,
    CrawlRequest,
    DependencyResponse,
    DocumentResponse,
)
from app.services.public import PublicService

router = APIRouter(
    prefix="/public",
    tags=["Public APIs"],
)

get_classifier = create_classifier_dependency("data/nace-structure.md")


@router.get("/dependencies", response_model=DependencyResponse)
async def fetch_dependencies(session: AsyncSession = Depends(get_session)):
    """
    # Get application dependencies

    Returns reference data needed by client applications including industries,
    countries and NACE activity classifications.

    **Returns:**
    - `industries`: List of industry classifications
    - `countries`: List of supported countries
    - `activities`: List of NACE activity codes
    """
    dependencies = await PublicService(session).fetch_dependencies()
    return dependencies


@router.post("/crawl", status_code=HTTPStatus.CREATED, response_model=CompanyRequest)
async def crawl_website(
    data: CrawlRequest,
    session: AsyncSession = Depends(get_session),
    classifier: Classifier = Depends(get_classifier),
):
    """
    # Crawl website for company information

    Analyzes a company website to extract business information using LLMs.

    **Parameters:**
    - `website`: Company website URL to analyze

    **Returns:**
    CompanyRequest with extracted company details and classifications
    """
    await classifier.initialize(session)
    company = await PublicService(session).crawl_website(data, classifier)
    return company


@router.post("/classify", status_code=HTTPStatus.CREATED, response_model=CompanyRequest)
async def classify(
    data: CompanyRequest,
    session: AsyncSession = Depends(get_session),
    classifier: Classifier = Depends(get_classifier),
):
    """
    # Classify company activities

    Analyzes company profile to determine NACE business classifications.

    **Parameters:**
    - Company details including description and objectives

    **Returns:**
    Company data enriched with matched NACE activity scopes
    """
    await classifier.initialize(session)
    company = await PublicService(session).classify_company(data, classifier)
    return company


@router.post("/policy", status_code=HTTPStatus.CREATED, response_model=DocumentResponse)
async def generate_policy(
    data: CompanyRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """
    # Generate policy document

    Creates a policy document based on company information.

    **Returns:**
    Success status with download URL for generated policy
    """

    document = await PublicService(session).create_policy(data, background_tasks=background_tasks)
    return document
