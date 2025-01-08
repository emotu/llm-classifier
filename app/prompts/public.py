"""
extractions.py

@author: Emotu Balogun
@created: December 11, 2024

Prompt templates for extracting company information and NACE activity codes.

This module contains prompt templates for extracting structured data about companies
and their economic activities. The prompts help parse company websites to identify
key business details and map them to standardized NACE Rev.2 activity codes.

Key Features:
    - Company information extraction (name, description, contacts, etc.)
    - Mapping of business activities to NACE codes
    - Structured output in JSON format
    - Validation of extracted company data

Usage:
    The prompts in this module are used by the LLM service to process company
    websites and extract standardized business information.

Example:
    >>> from app.prompts.extractions import prompt as extraction_prompt
    >>> result = llm.extract(extraction_prompt, company_url="example.com")
    >>> print(result.name)  # "Example Corp"
    >>> print(result.industry)  # "Software Development"

Notes:
    - Prompts are designed to handle various company website formats
    - Extraction focuses on publicly available information
    - Results are validated for completeness and accuracy
"""

crawler_prompt = """
Please extract the following information from the provided company website and return it in a structured JSON format. Include:

1. Company Name: The full legal name of the company.
2. Company Description: A brief overview of the company's activities, industry, and expertise.
3. Company Industries: An array of main sectors or industries the company operates in.
4. Company Objectives: The company's mission, vision, and core values.
5. Principal Person: The name and designation of the company's primary leader or spokesperson as `principal_person` and `principal_designation`.
6. Company Address: Include the primary office location if there are multiples, 
    or the address found on the site as structured address objects with `address_line_1`, `address_line_2`, `city`, `state`, `country`,
    and `postal_code`. `country` should be a 2-letter code. If the `state` is not provided, use a `region` value in the `state` field.
7. Contact Email: The primary contact email for the company.
8. Website: The company's official website URL.
9. Country: The country (2-letter code) the company is registered in.
10. Number of Employees: a range of number of employees in the company.

Format the output as follows:

{{
  "name": "string",
  "description": "string",
  "website": "string",
  "industries": ["string", "string"],
  "objectives": "string",
  "principal_person": "string",
  "principal_designation": "string"
  "address": {{
      "address_line_1": "string",
      "address_line_2": "string",
      "city": "string",
      "state": "string",
      "country": "string",
      "postal_code": "string"
  }},
  "country": "string",
  "contact_email": "string",
  "number_of_employees": "string"
}}

Map the industry to one of the following: 
{industries}

The company URL is: {company_url}. Extract only publicly available information, ensuring accuracy and completeness. 
For any fields that not available, return null as the value. DO NOT fill in the fields with placeholders.
"""


classify_prompt = """
Given the following business information, determine the most appropriate NACE Rev. 2 classification codes and titles.
Return as many appropriate classifications as possible using the provided context.

Business Name: {name}
Business Description: {description}
Business Industies: {industries}

Based on the NACE Rev. 2 classification context provided, please:

1. Identify the most appropriate NACE Rev. 2 classification codes and titles.
2. Return as many appropriate classifications as possible.
3. Return at least 5 classification codes structured as an array of strings with the value:
    - "code": The NACE Rev. 2 classification code.

Format your response as a JSON array of strings with the following structure:

["XX.XX","XX.XX","XX.XX",...]

"""

policy_prompt = """
Using the HTML template provided below, generate a new HTML document where:

1. Only the content within elements tagged with `data-ai-content="generated"` is modified.
2. The modifications must replace the text content with relevant, meaningful, and approximately equal-length generated content that maintains the original context.
3. All class names, image paths, DOM structure, and other attributes (including data-ai-content="generated") must remain unchanged.

Return only the modified HTML content, without any additional text or formatting.

Template:
{template}

"""
