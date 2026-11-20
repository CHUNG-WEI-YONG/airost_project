import base64
import json
import mimetypes
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from openai import OpenAI


def extract_receipt_details(receipt_file):
    if not settings.OPENAI_API_KEY:
        raise ImproperlyConfigured("OPENAI_API_KEY is not configured.")

    if not settings.OPENAI_BASE_URL:
        raise ImproperlyConfigured("OPENAI_BASE_URL is not configured.")

    if not settings.OPENAI_RECEIPT_MODEL:
        raise ImproperlyConfigured("OPENAI_RECEIPT_MODEL is not configured.")

    filename = receipt_file.name
    clean_filename = filename.replace("\\", "/").rsplit("/", 1)[-1]
    content_type, _ = mimetypes.guess_type(clean_filename)

    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    )

    if content_type == "application/pdf":
        with receipt_file.open("rb") as uploaded_file:
            provider_file = client.files.create(
                file=uploaded_file,
                purpose="rich_layout_recognition",
            )

        file_content = {
            "type": "input_file",
            "file_id": provider_file.id,
        }

    elif content_type in {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
    }:
        with receipt_file.open("rb") as uploaded_file:
            encoded_file = base64.b64encode(
                uploaded_file.read()
            ).decode("utf-8")

        file_content = {
            "type": "input_image",
            "image_url": f"data:{content_type};base64,{encoded_file}",
            "detail": "high",
        }

    else:
        raise ValueError("Upload a PDF, JPG, PNG, GIF, or WEBP receipt.")

    response = client.responses.create(
        model=settings.OPENAI_RECEIPT_MODEL,
        max_output_tokens=300,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Read this receipt. Return merchant, total_amount, "
                            "currency, and purchase_date as JSON. Do not guess. "
                            "Use null for missing or unclear values. "
                            "Return purchase_date as YYYY-MM-DD."
                        ),
                    },
                    file_content,
                ],
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "receipt_details",
                "schema": {
                    "type": "object",
                    "properties": {
                        "merchant": {"type": ["string", "null"]},
                        "total_amount": {"type": ["string", "null"]},
                        "currency": {"type": ["string", "null"]},
                        "purchase_date": {"type": ["string", "null"]},
                    },
                    "required": [
                        "merchant",
                        "total_amount",
                        "currency",
                        "purchase_date",
                    ],
                    "additionalProperties": False,
                },
            }
        },
    )

    result = json.loads(response.output_text)

    if not isinstance(result, dict):
        raise ValueError("The AI returned an unexpected result.")

    return result
