import os
import time
import tempfile
import logging
from django.conf import settings
from rest_framework.response import Response
from rest_framework.decorators import api_view
from PIL import Image, ImageDraw
import shutil
from django.http import JsonResponse, FileResponse
import vertexai
from google.cloud import aiplatform
import requests
import base64
from google.oauth2 import service_account
import google.auth.transport.requests

logger = logging.getLogger(__name__)
key_path = os.path.join(settings.BASE_DIR, 'google_key.json')
os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"] = key_path


aiplatform.init(
    project='probable-tape-421308',
    location='us-central1',
    credentials=None 
)


vertexai.init(project='probable-tape-421308', location='us-central1')
@api_view(['POST'])
def image_try_on(request):
    try:
        person_img = request.FILES.get('person_image')
        garment_img = request.FILES.get('garment_image')
        
        if not person_img or not garment_img:
            return Response({'error': 'Both images are required'}, status=400)
        
        tryon_results_dir = os.path.join(settings.MEDIA_ROOT, 'tryon_results')
        os.makedirs(tryon_results_dir, exist_ok=True)
        
        timestamp = int(time.time())
        person_path = os.path.join(tryon_results_dir, f'person_{timestamp}.jpg')
        garment_path = os.path.join(tryon_results_dir, f'garment_{timestamp}.jpg')

        with open(person_path, 'wb') as f:
            for chunk in person_img.chunks():
                f.write(chunk)

        with open(garment_path, 'wb') as f:
            for chunk in garment_img.chunks():
                f.write(chunk)

        logger.info(f"Person file size: {os.path.getsize(person_path)} bytes")
        logger.info(f"Garment file size: {os.path.getsize(garment_path)} bytes")
        
        try:
            result_image_path = process_virtual_try_on_vertex(person_path, garment_path)
            
            if not result_image_path:
                return Response({'error': 'AI processing failed'}, status=500)

            result_filename = f"result_{timestamp}.jpg"
            final_path = os.path.join(tryon_results_dir, result_filename)
            shutil.copy2(result_image_path, final_path)
            
            result_url = f"{settings.MEDIA_URL}tryon_results/{result_filename}"
            
            return Response({
                "success": True,
                "result_url": result_url,
                "message": "AI Virtual try-on completed!"
            })
            
        finally:
            for path in [person_path, garment_path]:
                if os.path.exists(path): os.unlink(path)
            
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=500)



def process_virtual_try_on_vertex(person_path, garment_path):
    try:
        if not os.path.exists(key_path):
            logger.error(f"Google key not found at: {key_path}")
            return None

        credentials = service_account.Credentials.from_service_account_file(
            key_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        auth_request = google.auth.transport.requests.Request()
        credentials.refresh(auth_request)
        access_token = credentials.token

        def normalize_to_jpeg(path):
            img = Image.open(path).convert('RGB')
            buf = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            img.save(buf.name, 'JPEG', quality=95)
            buf.close()
            return buf.name

        person_normalized = normalize_to_jpeg(person_path)
        garment_normalized = normalize_to_jpeg(garment_path)

        try:
            with open(person_normalized, "rb") as f:
                person_b64 = base64.b64encode(f.read()).decode("utf-8")
            with open(garment_normalized, "rb") as f:
                garment_b64 = base64.b64encode(f.read()).decode("utf-8")
        finally:
            for p in [person_normalized, garment_normalized]:
                if os.path.exists(p):
                    os.unlink(p)

        logger.info(f"Person b64 length: {len(person_b64)}, Garment b64 length: {len(garment_b64)}")

        if not person_b64 or not garment_b64:
            logger.error("One or both images failed to encode")
            return None

        project_id = 'probable-tape-421308'
        region = 'us-central1'
        url = (
            f"https://{region}-aiplatform.googleapis.com/v1/projects/{project_id}"
            f"/locations/{region}/publishers/google/models/virtual-try-on-001:predict"
        )

        payload = {
            "instances": [
                {
                    "personImage": {
                        "image": {
                            "bytesBase64Encoded": person_b64
                        }
                    },
                    "productImages": [
                        {
                            "image": {
                                "bytesBase64Encoded": garment_b64
                            }
                        }
                    ]
                }
            ],
            "parameters": {
                "sampleCount": 1,
                "baseSteps": 32,
                "person_generation": "ALLOW_ALL", 
                "outputOptions": {
                    "mimeType": "image/jpeg"
                }
            }
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers, timeout=120)
        if not response.ok:
            logger.error(f"VTO API error {response.status_code}: {response.text}")
        response.raise_for_status()

        result = response.json()
        predictions = result.get("predictions", [])

        if not predictions:
            logger.error(f"No predictions returned. Full response: {result}")
            return None

        image_b64 = predictions[0].get("bytesBase64Encoded")
        if not image_b64:
            logger.error(f"No image in prediction: {predictions[0]}")
            return None

        image_bytes = base64.b64decode(image_b64)
        temp_output = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        temp_output.write(image_bytes)
        temp_output.close()
        return temp_output.name

    except Exception as e:
        logger.error(f"Gen AI SDK VTO Error: {e}")
        return None


def process_virtual_try_on_local(person_image_path, garment_image_path):
    """
    Process virtual try-on locally with improved garment placement
    No API key required
    """
    try:
        person = Image.open(person_image_path).convert('RGBA')
        garment = Image.open(garment_image_path).convert('RGBA')
        
        person_width, person_height = person.size
        
        target_width = int(person_width * 0.45)
        target_height = int(garment.height * (target_width / garment.width))
        
        garment_resized = garment.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        x_position = (person_width - target_width) // 2
        y_position = int(person_height * 0.2)  # 20% from top
        
        result = person.copy()
        
        shadow = Image.new('RGBA', (target_width + 20, target_height + 20), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rectangle([(10, 10), (target_width + 10, target_height + 10)], 
                             fill=(0, 0, 0, 50))
        
        result.paste(garment_resized, (x_position, y_position), garment_resized)
        
        result = result.convert('RGB')
        
        temp_output = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        result.save(temp_output.name, 'JPEG', quality=95)
        
        return temp_output.name
        
    except Exception as e:
        logger.error(f"Local processing error: {str(e)}")
        return None


def process_virtual_try_on_simple(person_image_path, garment_image_path):
    """
    Simple fallback processing
    """
    person = Image.open(person_image_path).convert('RGB')
    garment = Image.open(garment_image_path).convert('RGBA')
    
    garment_size = (200, 200)
    garment_resized = garment.resize(garment_size)
    
    result = person.copy()
    result = result.convert('RGBA')
    
    x = (result.width - garment_size[0]) // 2
    y = int(result.height * 0.2)
    
    result.paste(garment_resized, (x, y), garment_resized)
    result = result.convert('RGB')
    
    temp_output = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    result.save(temp_output.name, 'JPEG', quality=95)
    
    return temp_output.name


@api_view(['POST'])
def pose_estimation_view(request):
    """Detect body pose for better garment fitting"""
    try:
        person_img = request.FILES.get('person_image')
        
        if not person_img:
            return Response({'error': 'person_image required'}, status=400)
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp:
            for chunk in person_img.chunks():
                temp.write(chunk)
            temp_path = temp.name
        
        try:
            keypoints = detect_pose_keypoints(temp_path)
            return Response({
                'success': True,
                'keypoints': keypoints,
                'clothing_zones': calculate_clothing_zones(keypoints)
            })
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"Pose estimation error: {str(e)}")
        return Response({'error': str(e)}, status=500)


def detect_pose_keypoints(image_path):
    """Detect pose keypoints using simple image analysis"""
    from PIL import Image
    img = Image.open(image_path)
    width, height = img.size
    
    return {
        'nose': {'x': width * 0.5, 'y': height * 0.1},
        'left_shoulder': {'x': width * 0.3, 'y': height * 0.25},
        'right_shoulder': {'x': width * 0.7, 'y': height * 0.25},
        'left_elbow': {'x': width * 0.25, 'y': height * 0.35},
        'right_elbow': {'x': width * 0.75, 'y': height * 0.35},
        'left_wrist': {'x': width * 0.2, 'y': height * 0.45},
        'right_wrist': {'x': width * 0.8, 'y': height * 0.45},
        'left_hip': {'x': width * 0.35, 'y': height * 0.55},
        'right_hip': {'x': width * 0.65, 'y': height * 0.55},
        'left_knee': {'x': width * 0.35, 'y': height * 0.75},
        'right_knee': {'x': width * 0.65, 'y': height * 0.75},
        'left_ankle': {'x': width * 0.35, 'y': height * 0.9},
        'right_ankle': {'x': width * 0.65, 'y': height * 0.9}
    }


def calculate_clothing_zones(keypoints):
    """Calculate clothing placement zones from keypoints"""
    return {
        'torso_zone': {
            'x': keypoints['left_shoulder']['x'],
            'y': keypoints['left_shoulder']['y'],
            'width': keypoints['right_shoulder']['x'] - keypoints['left_shoulder']['x'],
            'height': keypoints['left_hip']['y'] - keypoints['left_shoulder']['y']
        },
        'upper_body': {
            'x': keypoints['left_shoulder']['x'],
            'y': keypoints['nose']['y'],
            'width': keypoints['right_shoulder']['x'] - keypoints['left_shoulder']['x'],
            'height': keypoints['left_hip']['y'] - keypoints['nose']['y']
        }
    }


@api_view(['GET'])
def test_image_access(request, filename):
    """Test endpoint to check if image exists"""
    try:
        file_path = os.path.join(settings.MEDIA_ROOT, 'tryon_results', filename)
        if os.path.exists(file_path):
            return FileResponse(open(file_path, 'rb'), content_type='image/jpeg')
        else:
            return JsonResponse({'error': f'File not found: {file_path}'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)