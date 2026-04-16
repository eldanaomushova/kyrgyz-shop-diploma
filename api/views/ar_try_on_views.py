import os
import io
import base64
import logging
import tempfile
from PIL import Image
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.decorators.csrf import csrf_exempt
from google import genai
from google.genai import types
from dotenv import load_dotenv
import requests

load_dotenv()
logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def extract_garment_view(request):
    temp_file = None
    try:
        logger.info("=== extract_garment_view START ===")
        
        gemini_api_key = os.environ.get('GEMINI_API_KEY')
        remove_bg_api_key = os.environ.get('REMOVE_BGQUICK_API_KEY')
        
        logger.info(f"GEMINI_API_KEY present: {bool(gemini_api_key)}")
        logger.info(f"REMOVE_BGQUICK_API_KEY present: {bool(remove_bg_api_key)}, prefix: {remove_bg_api_key[:6] + '...' if remove_bg_api_key else 'MISSING'}")
        
        if not gemini_api_key:
            return Response({'error': 'GEMINI_API_KEY not configured'}, status=500)
        
        client = genai.Client(api_key=gemini_api_key)
        
        product_image = request.FILES.get('product_image')
        if not product_image:
            return Response({'error': 'No image provided'}, status=400)
        
        image_bytes = product_image.read()
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        response = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=[
                types.Part.from_bytes(data=img_byte_arr, mime_type='image/png'),
                "Extract the garment from this image and show it on a transparent background. Return ONLY the image."
            ],
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE', 'TEXT'],
                temperature=0.3,
            )
        )
        
        gemini_result = None
        for part in response.candidates[0].content.parts:
            if part.text:
                logger.info(f"Gemini text response: {part.text}")
            if part.inline_data and part.inline_data.data:
                gemini_result = part.inline_data.data
                logger.info(f"Gemini returned image: {len(gemini_result)} bytes")
                break
        
        if not gemini_result:
            return Response({'error': 'Gemini failed to extract garment'}, status=500)
        
        final_image = gemini_result
        background_removed = False
        
        if remove_bg_api_key:
            logger.info("Applying remove.bg for background removal")
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp.write(gemini_result)
                temp_path = tmp.name
            
            try:
                cleaned_path = remove_background(temp_path, remove_bg_api_key)
                if cleaned_path:
                    with open(cleaned_path, 'rb') as f:
                        final_image = f.read()
                    background_removed = True
                    logger.info("remove.bg successfully removed background")
                    os.unlink(cleaned_path)
                else:
                    logger.warning("remove.bg failed, using Gemini result as fallback")
            except Exception as e:
                logger.error(f"remove.bg error: {e}")
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        else:
            logger.warning("REMOVE_BGQUICK_API_KEY not set — skipping background removal")
        
        try:
            final_pil = Image.open(io.BytesIO(final_image))
            logger.info(f"Final image mode: {final_pil.mode}, size: {final_pil.size}")
            
            if not background_removed:
                if final_pil.mode in ('RGBA', 'LA', 'P'):
                    white_bg = Image.new('RGB', final_pil.size, (255, 255, 255))
                    if final_pil.mode == 'RGBA':
                        white_bg.paste(final_pil, mask=final_pil.split()[3])
                    else:
                        white_bg.paste(final_pil)
                    final_pil = white_bg
            
            output = io.BytesIO()
            final_pil.save(output, format='PNG', optimize=True)
            final_image = output.getvalue()
            
        except Exception as e:
            logger.warning(f"Image optimization failed: {e}")
        
        result_b64 = base64.b64encode(final_image).decode()
        
        return Response({
            "success": True,
            "image_url": f"data:image/png;base64,{result_b64}",
            "background_removed": background_removed
        })
        
    except Exception as e:
        logger.error(f"Extraction error: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=500)


def extract_garment(pil_image, garment_type='top'):
    try:
        if garment_type == 'top':
            garment_prompt = """Extract ONLY the top garment (shirt, t-shirt, blouse, jacket, sweater, etc.) from this image. 
            CRITICAL RULES:
            1. If the person is wearing multiple garments (e.g., shirt + pants/skirt), ONLY show the TOP garment
            2. Remove the person completely - no face, no hands, no body parts visible
            3. The garment should be flattened and displayed flat-lay style on a pure white background
            4. Do not show anyone holding the garment
            5. The garment should fill most of the frame
            6. Remove all background distractions
            7. The final image should look like a professional product photo of just the top garment on white background"""
        
        elif garment_type == 'bottom':
            garment_prompt = """Extract ONLY the bottom garment (pants, jeans, shorts, skirt, etc.) from this image.
            CRITICAL RULES:
            1. If the person is wearing multiple garments, ONLY show the BOTTOM garment
            2. Remove the person completely - no legs, no body parts visible
            3. The garment should be flattened and displayed flat-lay style on a pure white background
            4. Do not show anyone holding the garment
            5. Remove all background distractions
            6. The final image should look like a professional product photo of just the bottom garment on white background"""
        
        else:
            garment_prompt = """Extract the only 1 top garment from this image and show it on a plain white background.
            CRITICAL RULES:
            1. If multiple garments are visible, focus on the MAIN/PRIMARY garment
            2. Remove the person completely - no face, no hands, no body parts visible
            3. The garment should be flattened and displayed flat-lay style
            4. Do not show anyone holding the garment
            5. Remove all background distractions
            6. The final image should look like a professional product photo on white background"""
        
        client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
        
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()
        
        response = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type='image/png'),
                garment_prompt
            ],
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE', 'TEXT'],
                temperature=0.3,
            )
        )
        
        if response and response.candidates:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    img_bytes = part.inline_data.data
                    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                    tmp.write(img_bytes)
                    tmp.close()
                    logger.info(f"Gemini returned image - {len(img_bytes)} bytes")
                    return tmp.name
        
        logger.warning("Gemini returned no image")
        return None
        
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            logger.error("Gemini quota exceeded — billing not active yet")
        elif "404" in error_str:
            logger.error("Model not found - check model name")
        else:
            logger.error(f"Gemini extraction error: {e}", exc_info=True)
        return None


def remove_background(image_path, api_key=None):
    try:
        if not api_key:
            api_key = os.environ.get("REMOVE_BGQUICK_API_KEY")
        if not api_key:
            logger.warning("REMOVE_BGQUICK_API_KEY not set")
            return None

        with open(image_path, 'rb') as f:
            image_data = f.read()

        response = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            headers={"X-Api-Key": api_key},
            files={"image_file": ("image.png", image_data, "image/png")},
            data={
                "size": "auto",
                "type": "product",
                # bg_color intentionally omitted to preserve transparency
            },
            timeout=30,
        )

        if response.status_code != 200:
            logger.error(f"remove.bg API error {response.status_code}: {response.text}")
            return None

        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        tmp.write(response.content)
        tmp.close()

        logger.info(f"Background removed via remove.bg, output: {tmp.name}")
        return tmp.name

    except Exception as e:
        logger.error(f"Background removal failed: {e}")
        return None