import pathlib

from bs4 import BeautifulSoup
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.prompts import PromptTemplate

from app.llm.models import llm
from app.prompts.public import policy_prompt


class HTMLOutputParser(BaseOutputParser):
    """Parser for ensuring valid HTML output.

    This class extends BaseOutputParser to validate and clean HTML output from LLM responses.
    It handles common issues like removing markdown code blocks and ensures the output is
    well-formed HTML using BeautifulSoup.

    Methods:
        parse(text: str) -> str: Parses and validates the input text, returning clean HTML.
            Removes markdown formatting and validates HTML structure.
            Raises ValueError if invalid HTML is encountered.

    Example:
        >>> parser = HTMLOutputParser()
        >>> html = parser.parse("```html <div>content</div> ```")
        >>> print(html)  # Returns "<div>content</div>"
    """

    def parse(self, text: str) -> str:
        # Remove any markdown code blocks if present
        cleaned_text = text
        if cleaned_text.startswith("```html"):
            cleaned_text = cleaned_text.replace("```html", "", 1)
        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text.replace("```", "", 1)
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text.rsplit("```", 1)[0]

        # Validate and clean HTML
        try:
            soup = BeautifulSoup(cleaned_text.strip(), "html.parser")
            return str(soup)
        except Exception as e:
            raise ValueError(f"Invalid HTML content received: {e}")


async def generate_policy_template(template: str) -> str:
    """
    Generate a policy document from an HTML template using a Language Learning Model (LLM).

    This function takes an HTML template and uses an LLM to generate content for sections
    marked with the data-ai-content="generated" attribute. The original template structure
    and formatting are preserved, with only the marked sections being modified.

    Args:
        template (str): The name of the HTML template file to use. The template should be
                       located in the app/templates/print directory and contain sections
                       marked with data-ai-content="generated" where AI-generated content
                       should be inserted.

    Returns:
        str: The complete HTML document with AI-generated content inserted into the marked
             sections. All original HTML structure, classes, and attributes are preserved.

    Example:
        >>> html = await generate_policy_template("policy.html")
        >>> print(html)  # Returns complete HTML with AI-generated sections
    """
    policy_template = (
        pathlib.Path(__file__).parent.parent / "templates" / "print" / template
    ).read_text()

    prompt = PromptTemplate.from_template(policy_prompt)

    # Use the custom HTML parser
    output_parser = HTMLOutputParser()

    # Create the chain with the custom parser
    chain = prompt | llm | output_parser

    html_content = await chain.ainvoke({"template": policy_template})

    return html_content
