import os
import base64
import logging
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.decorators.csrf import csrf_exempt
from google import genai
from google.genai import types
import google.auth.transport.requests
import json
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


def get_vertex_client() -> genai.Client:
    creds_json_str = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    if creds_json_str:
        creds_info = json.loads(creds_json_str)
        credentials = service_account.Credentials.from_service_account_info(
            creds_info,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        project_id = creds_info.get('project_id')

    else:
        key_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if not key_path:
            raise EnvironmentError(
                "Set either GOOGLE_CREDENTIALS_JSON (Railway) "
                "or GOOGLE_APPLICATION_CREDENTIALS (local) env var."
            )
        import json as _json
        with open(key_path) as f:
            creds_info = _json.load(f)
        credentials = service_account.Credentials.from_service_account_file(
            key_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        project_id = creds_info.get('project_id')

    auth_request = google.auth.transport.requests.Request()
    credentials.refresh(auth_request)

    return genai.Client(
        vertexai=True,
        project=project_id,
        location='us-central1',
        credentials=credentials,
    )


@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def generate_cloth_image(request):
    try:
        sketch_file = request.FILES.get('sketch') or request.FILES.get('cloth_image')
        reference_file = request.FILES.get('reference_image')
        
        if not sketch_file:
            return Response({"error": "Sketch is required"}, status=400)

        client = get_vertex_client()
        sketch_bytes = sketch_file.read()
        
        if reference_file:
            ref_bytes = reference_file.read()
            
            prompt = """Using the first image as the SILHOUETTE/SKETCH and the second image as the COLOR + FABRIC reference, create a photorealistic garment that:
            1. EXACTLY matches the shape and silhouette from the sketch
            2. Uses the exact colors and fabric texture from the reference image
            3. Professional studio lighting on clean white background
            4. High-end fashion product photography style"""
            
            contents = [
                types.Part.from_bytes(data=sketch_bytes, mime_type="image/png"),
                types.Part.from_bytes(data=ref_bytes, mime_type="image/png"),
                prompt
            ]
        else:
            prompt = """You are a professional fashion designer and textile expert. Transform these input images into a PHOTOREALISTIC garment:
                INPUT 1 (SKETCH): The exact SILHOUETTE and SHAPE to follow
                INPUT 2 (REFERENCE): The COLOR, TEXTURE, and FABRIC TYPE to use

                REQUIREMENTS FOR OUTPUT:
                - EXACT silhouette match to the sketch - every curve, proportion, and line
                - Photorealistic fabric rendering with visible texture (weave, knit, or sheen)
                - Proper fabric draping and gravity-affected folds
                - Realistic lighting with soft shadows and highlights
                - Clean pure white background (RGB 255,255,255)
                - Professional studio lighting: key light at 45 degrees, fill light, rim light
                - High resolution, sharp focus, 8K quality
                - No mannequin or body visible - garment only (flat lay or invisible hanger)
                - Seamless, continuous fabric with no awkward warping
                - Natural fabric behavior at seams, hems, and edges

                TECHNICAL DETAILS:
                - Fabric weight appropriate for garment type
                - Thread tension and stitch details visible on close inspection
                - Natural color saturation (not over-saturated)
                - Realistic shadow casting on the white background
                - No artifacts, blurring, or AI distortions

                OUTPUT: A single high-quality PNG image of the realistic garment."""
            
            contents = [
                types.Part.from_bytes(data=sketch_bytes, mime_type="image/png"),
                prompt
            ]
        
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",  
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )
        
        image_data = None
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_data = part.inline_data.data
                    break
        
        if not image_data:
            text_response = ""
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_response += part.text
            return Response({
                "error": "No image generated. Gemini returned text instead.",
                "debug_response": text_response[:500]
            }, status=500)
        
        result_b64 = base64.b64encode(image_data).decode('utf-8')
        
        return Response({
            "success": True,
            "image_url": f"data:image/png;base64,{result_b64}",
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return Response({"error": str(e)}, status=500)