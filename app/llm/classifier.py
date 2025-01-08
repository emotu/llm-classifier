"""
classifier.py

@author: Emotu Balogun
@created: December 12, 2024

NACE Rev. 2 business activity classifier using large language models.

This module provides functionality to classify company business activities according to
standardized NACE Rev. 2 codes using LLM-based semantic analysis and retrieval.

Key Features:
    - Semantic search of NACE classification documents using FAISS vector store
    - LLM-based activity classification with configurable provider (OpenAI/Vertex AI)
    - Vector embeddings for efficient similarity search
    - Structured JSON output of matched NACE codes
    - Configurable chunk size and overlap for document processing

Usage:
    >>> classifier = Classifier("path/to/nace/docs")
    >>> company = CompanyRequest(
    ...     name="Tech Corp",
    ...     description="Software development",
    ...     industry="technology"
    ... )
    >>> codes = classifier.classify(company)
    >>> print(codes)  # ["62.01", "62.02", ...]

Example:
    Initialize classifier with NACE documentation:
    >>> classifier = Classifier("data/nace-v2-activities.md")

    Classify a company's activities:
    >>> company = CompanyRequest(
    ...     name="ALEC Engineering & Contracting",
    ...     description="Construction company specializing in complex projects",
    ...     industry="construction",
    ...     location="United Arab Emirates"
    ... )
    >>> codes = classifier.classify(company)

Note:
    Requires API key configuration for chosen LLM provider (OpenAI/Vertex AI).
    Provider can be configured via LLM_PROVIDER setting.
    Uses vector embeddings and LLMs for semantic search and classification.

:module: app.llm.classifier
:requires: langchain, faiss-cpu, openai/vertexai
"""

import json
import pathlib
from functools import lru_cache
from typing import Any

import slugify
from langchain.text_splitter import MarkdownTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_postgres.vectorstores import PGVector
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.llm.models import embeddings, llm
from app.prompts.public import classify_prompt, crawler_prompt
from app.schemas.public import ActionStatus, CompanyRequest


class Classifier:
    """
    Classifies company activities into standardized NACE codes using LLMs and vector search.

    Uses OpenAI for embeddings and language model inference, with FAISS for
    vector similarity search.
    """

    def __init__(self, document_path: str):
        """
        Initialize classifier with NACE documentation.

        Args:
            document_path: Path to markdown file containing NACE classification documentation
            db_session: AsyncSession for database operations
        """
        self.llm = llm
        self.embeddings = embeddings
        self.collection_name = "nace_documents"
        self.document_path = document_path
        self.session: AsyncSession | None = None
        self.vector_store: PGVector | None = None
        self.retriever = None

    async def initialize(self, session: AsyncSession):
        """
        Async initialization of the vector store and retriever.
        """
        self.session = session
        self.vector_store = await self._get_or_create_vector_store()
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})

    async def _check_collection_exists(self) -> Any | None:
        """
        Check if the collection already exists and has documents.
        """
        try:
            query = text("""
            SELECT EXISTS (
                SELECT 1 
                FROM langchain_pg_embedding e
                JOIN langchain_pg_collection c ON c.uuid = e.collection_id
                WHERE c.name = :collection_name 
                LIMIT 1
            )
            """)

            result = await self.session.execute(
                query, {"collection_name": self.collection_name}
            )
            return result.scalar()
        except Exception as e:
            print(f"Error checking collection existence: {e}")
            return False

    async def _get_or_create_vector_store(
        self, chunk_size: int = 2000, chunk_overlap: int = 200
    ):
        """
        Get existing vector store or create new one if it doesn't exist.
        """

        vector_store = PGVector(
            collection_name=self.collection_name,
            embeddings=self.embeddings,
            connection=settings.VECTOR_STORE_URL,
            use_jsonb=True,
        )

        # First try to get existing store
        if await self._check_collection_exists():
            return vector_store

        # If no existing documents, create new store
        loader = TextLoader(self.document_path)
        documents = loader.load()

        text_splitter = MarkdownTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        texts = text_splitter.split_documents(documents)

        vector_store = await PGVector.afrom_documents(
            documents=texts,
            collection_name=self.collection_name,
            embedding=self.embeddings,
            connection=settings.VECTOR_STORE_URL,
            connection_kwargs={"echo": settings.DB_ECHO},
            use_jsonb=True,
        )

        return vector_store

    def _build_prompt(self, prompt: str, input: CompanyRequest | dict) -> str:
        """
        Format prompt template with input data.

        Args:
            prompt: Template string with placeholders
            input: Company data as CompanyRequest or dict

        Returns:
            Formatted prompt string
        """
        data = input.model_dump() if isinstance(input, CompanyRequest) else input
        return prompt.format(**data)

    def get_industries(self) -> str:
        """
        Get the list of industries from the industries.txt file.
        """
        source_path = (
            pathlib.Path(__file__).parent.parent.parent / "data" / "industries.json"
        ).read_text()
        industries = json.loads(source_path)

        return "\n".join([slugify.slugify(x, separator="_") for x in industries])

    async def crawl(self, company_url: str) -> CompanyRequest:
        """
        Crawl a company's website and extract relevant information.
        """

        prompt = PromptTemplate.from_template(crawler_prompt)
        industries = self.get_industries()
        chain = prompt | self.llm | JsonOutputParser()
        return await chain.ainvoke({
            "company_url": company_url,
            "industries": industries,
        })

    async def classify(
        self, input: CompanyRequest | dict
    ) -> CompanyRequest | ActionStatus | None:
        """
        Classify company activities into NACE codes using LLM chain.

        Args:
            input: Company data as CompanyRequest or dict containing name,
                  description and industry

        Returns:
            CompanyRequest with matched NACE codes in scopes field, or
            ActionStatus on error

        Raises:
            Exception: If classification fails
        """
        try:
            prompt_input = self._build_prompt(classify_prompt, input)

            prompt = PromptTemplate.from_template("""
                Context:
                {context}

                Question:
                {question}
            """)

            retrieval_chain = RunnablePassthrough() | {
                "context": lambda x: "\n".join(
                    doc.page_content for doc in self.retriever.invoke(prompt_input)
                ),
                "question": lambda _: prompt_input,
            }

            chain = retrieval_chain | prompt | self.llm | JsonOutputParser()
            company = CompanyRequest.model_validate(input)
            company.scopes = await chain.ainvoke({})

            return company
        except Exception as e:
            action_status = ActionStatus(
                status="error", payload={"description": str(e)}
            )
            return action_status


def create_classifier_dependency(document_path: str):
    """
    Create a cached dependency provider for the Classifier.

    Args:
        document_path (str): Path to the document containing NACE classifications

    Returns:
        Callable: Factory function that returns an initialized Classifier instance
    """
    base_path = pathlib.Path(__file__).parent.parent.parent
    document_path = str((base_path / document_path).resolve())

    @lru_cache(maxsize=1)
    def get_classifier():
        classifier = Classifier(document_path)
        return classifier

    return get_classifier
