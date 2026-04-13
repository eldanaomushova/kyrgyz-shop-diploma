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
from rembg import remove
from rembg import remove, new_session
import numpy as np

load_dotenv()

logger = logging.getLogger(__name__)

client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY"),
)

@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def extract_garment_view(request):
    result_path = None
    try:
        product_image = request.FILES.get('product_image')
        if not product_image:
            return Response({'error': 'No image provided'}, status=400)
        
        garment_type = request.POST.get('garment_type', 'top')  
        
        image_bytes = product_image.read()

        try:
            pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            return Response({'error': f'Invalid image: {str(e)}'}, status=400)

        result_path = extract_garment(pil_image, garment_type)

        if not result_path:
            return Response({'error': 'Garment extraction failed'}, status=500)

        cleaned_path = remove_background(result_path)
        
        if cleaned_path and os.path.exists(cleaned_path):
            result_path = cleaned_path

        with open(result_path, 'rb') as f:
            result_b64 = base64.b64encode(f.read()).decode()

        return Response({
            "success": True,
            "image_url": f"data:image/png;base64,{result_b64}",
            "garment_type": garment_type
        })

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=500)

    finally:
        if result_path and os.path.exists(result_path):
            os.unlink(result_path)


def remove_background(image_path):
    """Remove background from image using rembg"""
    try:
        with open(image_path, 'rb') as f:
            input_image = f.read()
        
        output_image = remove(input_image)
        
        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        tmp.write(output_image)
        tmp.close()
        
        logger.info(f"✅ Background removed - {len(output_image)} bytes")
        return tmp.name
    except Exception as e:
        logger.error(f"Background removal failed: {e}")
        return None


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
        
        buf = io.BytesIO()
        pil_image.save(buf, format="JPEG", quality=95)
        image_bytes = buf.getvalue()

        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                types.Part.from_text(text=garment_prompt),
            ],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
                temperature=0.3,  
                top_p=0.95,
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.text:
                logger.info(f"Gemini text response: {part.text}")
            
            if part.inline_data and part.inline_data.data:
                img_bytes = part.inline_data.data
                tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                tmp.write(img_bytes)
                tmp.close()
                logger.info(f"✅ Gemini returned image - {len(img_bytes)} bytes")
                return tmp.name

        logger.warning("Gemini returned no image")
        return None

    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            logger.error("⚠️ Gemini quota exceeded — billing not active yet")
        elif "404" in error_str:
            logger.error("⚠️ Model not found")
        else:
            logger.error(f"Gemini extraction error: {e}", exc_info=True)
        return None


def extract_garment_with_segmentation(pil_image, garment_type='top'):
    try:
        session = new_session("u2net") 
        
        output = remove(pil_image, session=session)
        
        output_np = np.array(output)
        
        alpha = output_np[:, :, 3] if output_np.shape[2] == 4 else np.ones(output_np.shape[:2]) * 255
        non_transparent = np.where(alpha > 0)
        
        if len(non_transparent[0]) > 0:
            y_min, y_max = max(0, non_transparent[0].min() - 10), min(output_np.shape[0], non_transparent[0].max() + 10)
            x_min, x_max = max(0, non_transparent[1].min() - 10), min(output_np.shape[1], non_transparent[1].max() + 10)
            
            cropped = output.crop((x_min, y_min, x_max, y_max))
            white_bg = Image.new('RGBA', cropped.size, (255, 255, 255, 255))
            white_bg.paste(cropped, (0, 0), cropped)
            
            tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            white_bg.convert('RGB').save(tmp, format='PNG')
            tmp.close()
            
            logger.info(f"✅ Segmentation extraction successful")
            return tmp.name
        
        return None
        
    except Exception as e:
        logger.error(f"Segmentation extraction failed: {e}")
        return None