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
import requests

logger = logging.getLogger(__name__)

GEMINI_IMAGE_MODEL = 'gemini-2.5-flash-image'

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
        logger.info(f"REMOVE_BGQUICK_API_KEY present: {bool(remove_bg_api_key)}")
        
        if not gemini_api_key:
            return Response({'error': 'GEMINI_API_KEY not configured'}, status=500)
        
        client = genai.Client(api_key=gemini_api_key)
        
        product_image = request.FILES.get('product_image')
        if not product_image:
            return Response({'error': 'No image provided'}, status=400)
        
        image_bytes = product_image.read()
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # Resize large images to avoid timeouts
        max_size = (1024, 1024)
        if pil_image.size[0] > max_size[0] or pil_image.size[1] > max_size[1]:
            pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
            logger.info(f"Image resized to: {pil_image.size}")
        
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        try:
            response = client.models.generate_content(
                model=GEMINI_IMAGE_MODEL,
                contents=[
                    types.Part.from_bytes(data=img_byte_arr, mime_type='image/png'),
                    "Extract the main garment from this image and show it on a transparent background. Remove the person completely. Return ONLY the image."
                ],
                config=types.GenerateContentConfig(
                    response_modalities=['IMAGE', 'TEXT'],
                    temperature=0.3,
                )
            )
        except Exception as api_error:
            logger.error(f"Gemini API call failed: {api_error}")
            return Response({
                'error': 'Gemini API call failed',
                'detail': str(api_error)
            }, status=500)
        
        # Check if response is valid
        if not response:
            logger.error("Gemini returned None response")
            return Response({'error': 'Gemini API returned no response'}, status=500)
        
        # Check candidates
        if not response.candidates:
            logger.error("No candidates in Gemini response")
            logger.error(f"Full response: {response}")
            return Response({'error': 'No candidates in Gemini response'}, status=500)
        
        candidate = response.candidates[0]
        
        # Check finish reason
        if hasattr(candidate, 'finish_reason') and candidate.finish_reason:
            finish_reason = str(candidate.finish_reason)
            logger.warning(f"Gemini finish reason: {finish_reason}")
            
            if 'SAFETY' in finish_reason:
                logger.error("Content blocked by safety filters")
                return Response({
                    'error': 'Content blocked by safety filters',
                    'detail': 'The image was blocked by safety filters. Please try with a different image.'
                }, status=400)
            elif 'RECITATION' in finish_reason:
                logger.error("Content blocked due to recitation/copyright")
                return Response({
                    'error': 'Content blocked due to copyright concerns',
                    'detail': 'The image may contain copyrighted content.'
                }, status=400)
            elif 'STOP' in finish_reason:
                logger.info("Generation stopped normally")
        
        # CRITICAL: Check if content exists
        if not candidate.content:
            logger.error("Candidate has no content - likely blocked by safety filters")
            
            if hasattr(candidate, 'safety_ratings') and candidate.safety_ratings:
                logger.error(f"Safety ratings: {candidate.safety_ratings}")
            
            return Response({
                'error': 'Gemini could not process this image',
                'detail': 'The image may have been blocked by safety filters.'
            }, status=400)
        
        # Extract image data
        gemini_result = None
        for part in candidate.content.parts:
            if hasattr(part, 'text') and part.text:
                logger.info(f"Gemini text response: {part.text}")
            if hasattr(part, 'inline_data') and part.inline_data and part.inline_data.data:
                gemini_result = part.inline_data.data
                logger.info(f"Gemini returned image: {len(gemini_result)} bytes")
                break
        
        if not gemini_result:
            logger.error("No image data in Gemini response")
            return Response({'error': 'Gemini failed to extract garment - no image returned'}, status=500)
        
        final_image = gemini_result
        background_removed = False
        
        # Optional: Apply remove.bg for cleaner results
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
        
        # Process final image
        try:
            final_pil = Image.open(io.BytesIO(final_image))
            logger.info(f"Final image mode: {final_pil.mode}, size: {final_pil.size}")
            
            # Convert to RGB with white background if no transparency
            if not background_removed and final_pil.mode in ('RGBA', 'LA', 'P'):
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
    """Extract garment using Gemini - FIXED to use correct model"""
    try:
        if garment_type == 'top':
            garment_prompt = """Extract ONLY the top garment (shirt, t-shirt, blouse, jacket, sweater, etc.) from this image. 
            CRITICAL RULES:
            1. If the person is wearing multiple garments, ONLY show the TOP garment
            2. Remove the person completely - no face, no hands, no body parts visible
            3. The garment should be displayed on a pure white background
            4. The garment should fill most of the frame
            5. The final image should look like a professional product photo"""
        
        elif garment_type == 'bottom':
            garment_prompt = """Extract ONLY the bottom garment (pants, jeans, shorts, skirt, etc.) from this image.
            CRITICAL RULES:
            1. If the person is wearing multiple garments, ONLY show the BOTTOM garment
            2. Remove the person completely - no legs, no body parts visible
            3. The garment should be displayed on a pure white background
            4. The final image should look like a professional product photo"""
        
        else:
            garment_prompt = """Extract the main garment from this image.
            CRITICAL RULES:
            1. Remove the person completely - no face, no hands, no body parts visible
            2. The garment should be displayed on a pure white background
            3. The final image should look like a professional product photo"""
        
        gemini_api_key = os.environ.get('GEMINI_API_KEY')
        if not gemini_api_key:
            logger.error("GEMINI_API_KEY not configured")
            return None
            
        client = genai.Client(api_key=gemini_api_key)
        
        # Resize if too large
        max_size = (1024, 1024)
        if pil_image.size[0] > max_size[0] or pil_image.size[1] > max_size[1]:
            pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()
        
        # FIXED: Use the correct model name
        response = client.models.generate_content(
            model=GEMINI_IMAGE_MODEL,  # Now uses correct model
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type='image/png'),
                garment_prompt
            ],
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE', 'TEXT'],
                temperature=0.3,
            )
        )
        
        # Check if response is valid
        if not response or not response.candidates:
            logger.error("Invalid response from Gemini")
            return None
            
        candidate = response.candidates[0]
        
        # Check finish reason
        if hasattr(candidate, 'finish_reason') and candidate.finish_reason:
            finish_reason = str(candidate.finish_reason)
            logger.warning(f"Gemini finish reason: {finish_reason}")
            if 'SAFETY' in finish_reason or 'RECITATION' in finish_reason:
                logger.error(f"Content blocked: {finish_reason}")
                return None
        
        # Check if content exists
        if not candidate.content:
            logger.error("Candidate has no content")
            return None
        
        # Extract image
        for part in candidate.content.parts:
            if hasattr(part, 'inline_data') and part.inline_data and part.inline_data.data:
                img_bytes = part.inline_data.data
                tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                tmp.write(img_bytes)
                tmp.close()
                logger.info(f"Successfully extracted garment - {len(img_bytes)} bytes")
                return tmp.name
        
        logger.warning("Gemini returned no image")
        return None
        
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            logger.error("Gemini quota exceeded — billing not active yet")
        elif "404" in error_str:
            logger.error(f"Model {GEMINI_IMAGE_MODEL} not found")
        else:
            logger.error(f"Gemini extraction error: {e}", exc_info=True)
        return None


def remove_background(image_path, api_key=None):
    """Remove background using remove.bg API"""
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
            },
            timeout=30,
        )

        if response.status_code != 200:
            logger.error(f"remove.bg API error {response.status_code}: {response.text}")
            return None

        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        tmp.write(response.content)
        tmp.close()

        logger.info(f"Background removed via remove.bg")
        return tmp.name

    except Exception as e:
        logger.error(f"Background removal failed: {e}")
        return None