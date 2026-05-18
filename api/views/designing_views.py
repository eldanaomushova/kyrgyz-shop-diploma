import os
import json
import logging
from PIL import Image
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.decorators.csrf import csrf_exempt
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

client = genai.Client()

GEMINI_IMAGE_MODEL = 'gemini-2.5-flash' 

@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def generate_design(request):
    try:
        image_file = request.FILES.get('cloth_image')
        if not image_file:
            return Response(
                {"error": "No image file provided under 'cloth_image'"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            pil_image = Image.open(image_file)
        except Exception as img_err:
            logger.error(f"Failed to open image file: {str(img_err)}")
            return Response(
                {"error": "Invalid image file format."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        prompt_text = (
            "You are a fashion design assistant. The user has drawn a clothing sketch.\n"
            "Analyze it and respond ONLY with a JSON object:\n"
            "{\n"
            "  \"garmentType\": \"short type label e.g. Dress, Jacket, T-Shirt\",\n"
            "  \"description\": \"2-3 sentence vivid description of the garment\",\n"
            "  \"imagePrompt\": \"detailed prompt for generating a photorealistic version of this garment\"\n"
            "}"
        )

        response = client.models.generate_content(
            model=GEMINI_IMAGE_MODEL,
            contents=[pil_image, prompt_text],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

        try:
            analysis_data = json.loads(response.text)
        except json.JSONDecodeError:
            cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
            analysis_data = json.loads(cleaned_text)

        return Response(analysis_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error during design generation: {str(e)}")
        return Response(
            {"error": "Internal server error during AI analysis."}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )