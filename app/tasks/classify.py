import pathlib
import uuid

from jinja2 import Environment, PackageLoader, select_autoescape

from app.config import settings
from app.llm.generator import generate_policy_template
from app.models import create_session
from app.models.assets import Company, Document
from app.utils.email import send_email
from app.utils.pdf import generate_pdf, upload_pdf

env = Environment(
    loader=PackageLoader("app", "templates"),
    autoescape=select_autoescape(["html", "xml"]),
)


async def generate_policy(document_id: str | uuid.UUID) -> Document:
    session = await create_session()
    try:
        document: Document | None = await session.get(Document, document_id)
        if not document:
            raise ValueError("Document not found")

        company: Company | None = await session.get(Company, document.company_id)
        if not company:
            raise ValueError("Company not found")

        if not company.contact_email:
            raise ValueError("Company contact email not found")

        policy_template = await generate_policy_template("policy.html")
        base_path = pathlib.Path(__file__).parent.parent / "static"
        context = {
            "company": company,
            "document": document,
            "base_path": f"file://{base_path}",
        }

        template = env.from_string(policy_template)
        content = template.render(context)

        doc = generate_pdf(content)

        filename = document.filename
        if not filename:
            raise ValueError("Filename not found")

        # Send email with policy document
        await send_email(
            "email/policy.html",
            to=company.contact_email,
            subject=settings.POLICY_EMAIL_SUBJECT,
            context=dict(document=document, company=company),
            attachments=[{"filename": filename, "content": list(doc)}],
        )

        document.download_url = upload_pdf(filename, doc)
        document.content = content
        document.status = "completed"
        session.add(document)
        await session.commit()

        return document
    finally:
        await session.close()
