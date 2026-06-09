import os
import base64
import logging
import requests
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.decorators.csrf import csrf_exempt
from google import genai
from google.genai import types
import tempfile
import json
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


def remove_background_from_bytes(image_bytes: bytes, api_key: str) -> bytes | None:
    try:
        response = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            headers={"X-Api-Key": api_key},
            files={"image_file": ("image.png", image_bytes, "image/png")},
            data={"size": "auto", "type": "product"},
            timeout=30,
        )

        if response.status_code == 402:
            logger.warning("remove.bg quota exhausted (402). Top up at remove.bg/pricing.")
            return None
        if response.status_code != 200:
            logger.error(f"remove.bg error {response.status_code}: {response.text[:200]}")
            return None

        return response.content

    except Exception as e:
        logger.error(f"remove_background_from_bytes exception: {e}")
        return None


@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def extract_garment_view(request):
    try:
        product_image = request.FILES.get('product_image')
        garment_type = request.data.get('garment_type', 'garment')

        if not product_image:
            return Response({'error': 'No image provided'}, status=400)

        image_bytes = product_image.read()
        mime_type = product_image.content_type or 'image/jpeg'

        client = genai.Client(
            vertexai=True,
            project='my-second-project-497114',
            location='us-central1'
        )

        logger.info("Generating studio photo via Gemini image generation...")

        prompt = (
            f"This is a {garment_type}. Generate a high-quality studio e-commerce "
            "product photo of this exact garment displayed flat or on a white background. "
            "No human model, no skin, no faces. Keep the garment's design, color, and "
            "details accurate. Professional product photography style."
        )

        response = client.models.generate_content(
            model='gemini-2.5-flash-image',  
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt,
            ],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        generated_bytes = None
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                generated_bytes = part.inline_data.data
                break

        if not generated_bytes:
            text_response = response.text if hasattr(response, 'text') else 'none'
            logger.error(f"No image in response. Text: {text_response}")
            return Response({'error': 'Model did not return an image'}, status=500)

        remove_bg_key = os.environ.get('REMOVE_BG_API_KEY')
        final_bytes = generated_bytes
        bg_removed = False

        if remove_bg_key:
            logger.info("Removing background via remove.bg...")
            cleaned = remove_background_from_bytes(generated_bytes, remove_bg_key)
            if cleaned:
                final_bytes = cleaned
                bg_removed = True
                logger.info("Background removed successfully.")
            else:
                logger.warning("Background removal failed — using raw model output.")
        else:
            logger.warning("REMOVE_BG_API_KEY not set — skipping background removal.")

        result_b64 = base64.b64encode(final_bytes).decode('utf-8')

        return Response({
            "success": True,
            "image_url": f"data:image/png;base64,{result_b64}",
            "background_removed": bg_removed,
            "model_used": "Gemini 2.5 Flash + remove.bg"
        })

    except Exception as e:
        logger.error(f"Critical Exception: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=500)


def remove_background(image_path: str, api_key: str) -> str | None:
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()

        cleaned = remove_background_from_bytes(image_data, api_key)
        if not cleaned:
            return None

        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        tmp.write(cleaned)
        tmp.close()
        return tmp.name

    except Exception as e:
        logger.error(f"remove_background exception: {e}")
        return None