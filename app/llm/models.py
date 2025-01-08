"""
Models Module

This module centralizes the instantiation of language models and embeddings across the application.
It provides a single source of truth for managing model setup and configuration.

The module initializes both Google Vertex AI and OpenAI models with consistent parameters,
allowing for easy switching between providers.

Models:
    - vertex_llm: Google Vertex AI language model instance
    - openai_llm: OpenAI language model instance
    - vertex_embeddings: Google Vertex AI embeddings model
    - openai_embeddings: OpenAI embeddings model

Configuration is pulled from app settings to maintain consistency across the application.
Safety settings are configured for Vertex AI to allow unrestricted content generation.
"""

# import vertexai
# from langchain_google_vertexai import HarmBlockThreshold, HarmCategory, VertexAI
# from langchain_google_vertexai.embeddings import VertexAIEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.config import settings

# vertexai.init(project=settings.GCP_PROJECT_ID, location=settings.GCP_PROJECT_LOCATION)

# safety_settings = {
#     HarmCategory.HARM_CATEGORY_UNSPECIFIED: HarmBlockThreshold.BLOCK_NONE,
#     HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
#     HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
#     HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
#     HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
# }


# _vertex_llm = VertexAI(
#     model_name=settings.VERTEX_LLM_MODEL,
#     max_output_tokens=2048,
#     temperature=0.1,
#     top_p=0.95,
#     top_k=40,
#     safety_settings=safety_settings,
# )
_openai_llm = ChatOpenAI(
    api_key=settings.OPENAI_API_KEY,
    model_name=settings.OPENAI_LLM_MODEL,
    temperature=0.1,
    max_tokens=2048,
)

# _vertex_embeddings = VertexAIEmbeddings(model_name=settings.VERTEX_EMBEDDING_MODEL)
_openai_embeddings = OpenAIEmbeddings(
    api_key=settings.OPENAI_API_KEY,
    model=settings.OPENAI_EMBEDDING_MODEL,
)

_embedding_providers = dict(
    # vertex=_vertex_embeddings,
    openai=_openai_embeddings,
)

llm_providers = dict(
    # vertex=_vertex_llm,
    openai=_openai_llm,
)

# Use the provider specified in settings
llm = llm_providers[settings.LLM_PROVIDER]
embeddings = _embedding_providers[settings.LLM_PROVIDER]
