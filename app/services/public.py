# Used for generating mock company data
from datetime import datetime
from functools import lru_cache

import shortuuid
from fastapi import BackgroundTasks, HTTPException, status
from pydantic_extra_types.country import _countries
from sqlmodel import or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.llm.classifier import Classifier
from app.models.assets import Company, Document, Industry, Scope
from app.schemas.public import (
    ActionStatus,
    CompanyRequest,
    CrawlRequest,
    DependencyResponse,
)
from app.tasks.classify import generate_policy


class PublicService:
    """Service class for handling public API operations.

    This class provides methods for accessing public data and services like company information,
    dependencies, and document generation.

    Attributes:
        session (AsyncSession): The database session for database operations
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the PublicService.

        Args:
            session (AsyncSession): Database session for async database operations
        """
        self.session = session

    async def fetch_scopes(self, query: str | None = None):
        """Fetch NACE scopes with optional text search.

        Args:
            query (str | None): Optional search string to filter scopes. Defaults to None.

        Returns:
            List of matching Scope objects from the database.
        """
        statement = select(Scope)

        if query:
            query_string = f"%{query}%"
            statement = statement.where(
                or_(
                    Scope.name.ilike(query_string),
                    Scope.description.ilike(query_string),
                )
            )

    @lru_cache(maxsize=100)
    async def fetch_dependencies(self) -> DependencyResponse:
        """Fetch application dependencies and reference data.

        Retrieves all dependencies and reference data needed by client applications,
        including industry classifications and country lists.

        Returns:
            DependencyResponse: Object containing:
                - industries: List of available industry classifications
                - countries: List of supported countries with metadata
                - scopes: List of NACE scope classifications

        Example:
            ```python
            service = PublicService(session)
            dependencies = await service.fetch_dependencies()
            print(dependencies.industries)  # List of industry objects
            print(dependencies.countries)   # List of country objects
            ```

        Notes:
            - Industries are sorted alphabetically by name
            - Countries list is static and includes standard ISO country codes
            - Results are cached using lru_cache
        """
        statement = select(Industry).order_by(Industry.name)
        industries = await self.session.exec(statement)
        countries = _countries()

        nstatement = select(Scope).order_by(Scope.class_code)
        scopes = await self.session.exec(nstatement)
        return dict(
            industries=industries.fetchall(),
            countries=countries,
            scopes=scopes.fetchall(),
        )

    async def crawl_website(
        self, data: CrawlRequest, classifier: Classifier
    ) -> CompanyRequest:
        """Crawl a website to extract company information.

        Uses the provided classifier to analyze a website and extract structured
        company information.

        Args:
            data (CrawlRequest): Request containing the website URL to analyze
            classifier (Classifier): Classifier instance for analyzing website content

        Returns:
            CompanyRequest: Structured company information extracted from the website
        """
        try:
            company = await classifier.crawl(data.website.unicode_string())
            return company
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ActionStatus(
                    status="failed",
                    code="WEBSITE_CRAWL_ERROR",
                    description=str(e),
                    payload=data.model_dump(),
                ).model_dump(),
            )

    async def classify_company(
        self, data: CompanyRequest, classifier: Classifier
    ) -> CompanyRequest | ActionStatus | None:
        """Classify a company's business activities.

        Uses the provided classifier to analyze company information and determine
        appropriate business activity classifications.

        Args:
            data (CompanyRequest): Company information to classify
            classifier (Classifier): Classifier instance for analyzing company data

        Returns:
            CompanyRequest: Company information enriched with classifications
        """
        company = await classifier.classify(data)

        return company

    async def create_policy(
        self, data: CompanyRequest, background_tasks: BackgroundTasks | None = None
    ) -> Document:
        """Create a policy document for a company.

        Generates a new policy document based on the provided company information
        and stores it in the database.

        Args:
            data (CompanyRequest): Company information for policy generation

        Returns:
            Document: Created document record with pending status

        Notes:
            - Creates both Company and Document records
            - Document status is set to 'pending' initially
            - Document URL is generated using the BASE_URL setting
        """
        company = Company(**data.model_dump())
        self.session.add(company)
        await self.session.commit()

        version = shortuuid.ShortUUID().random(length=12)
        policy = Document(
            company_id=company.id,
            name=f"Quality Policy - {company.name} - {datetime.now().strftime('%Y-%m-%d %H-%M-%S')}.pdf",
            description=f"ISO compliant policy document for {company.name}",
            download_url=None,
            filename=f"doc-{version}.pdf",
            mime_type="application/pdf",
            source="generated",
            status="pending",
        )
        self.session.add(policy)
        await self.session.commit()

        policy = await generate_policy(policy.id)
        return policy

        # if not background_tasks:
        #     policy = await generate_policy(policy.id)
        #     return policy

        # background_tasks.add_task(generate_policy, policy.id)
        # return policy
