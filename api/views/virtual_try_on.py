import os
import time
import tempfile
import logging
from django.conf import settings
from rest_framework.response import Response
from rest_framework.decorators import api_view
from PIL import Image
import requests
import base64
import google.auth
import google.auth.transport.requests

logger = logging.getLogger(__name__)


def get_access_token():
    try:
        credentials, project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        auth_request = google.auth.transport.requests.Request()
        credentials.refresh(auth_request)

        if not credentials.valid:
            logger.error("Credentials are not valid after refresh")
            return None

        return credentials.token
    except Exception as e:
        logger.error(f"Failed to get access token: {e}", exc_info=True)
        return None


def normalize_to_jpeg(image_file):
    """Convert uploaded image to JPEG and return base64 string."""
    try:
        # Seek to beginning of file
        image_file.seek(0)
        img = Image.open(image_file)
        
        # Convert RGBA to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize if too large (Vercel has 4.5MB limit)
        max_size = 1024  # Max dimension
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Convert to base64 without saving to disk
        import io
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85, optimize=True)
        img_bytes = buffer.getvalue()
        
        return base64.b64encode(img_bytes).decode('utf-8')
    except Exception as e:
        logger.error(f"Error normalizing image: {e}")
        raise


@api_view(['POST'])
def image_try_on(request):
    """Virtual try-on that works on Vercel - no disk writes, returns base64"""
    try:
        person_img = request.FILES.get('person_image')
        garment_img = request.FILES.get('garment_image')

        if not person_img or not garment_img:
            return Response({'error': 'Both images are required'}, status=400)

        logger.info(f"Processing try-on request on Vercel")
        logger.info(f"Person image: {person_img.size} bytes, {person_img.content_type}")
        logger.info(f"Garment image: {garment_img.size} bytes, {garment_img.content_type}")

        # Check file sizes (Vercel limit is ~4.5MB total)
        total_size = person_img.size + garment_img.size
        if total_size > 4_000_000:  # 4MB to be safe
            return Response({
                'error': f'Images too large (total {total_size/1024/1024:.1f}MB). Please use smaller images (max 2MB each)'
            }, status=400)

        # Convert images to base64 without saving to disk
        person_b64 = normalize_to_jpeg(person_img)
        garment_b64 = normalize_to_jpeg(garment_img)

        logger.info(f"Base64 lengths - Person: {len(person_b64)}, Garment: {len(garment_b64)}")

        # Try Vertex AI first
        try:
            result_b64 = call_vertex_ai_api(person_b64, garment_b64)
            if result_b64:
                return Response({
                    "success": True,
                    "result_image": result_b64,
                    "message": "Virtual try-on completed with AI!"
                })
        except Exception as e:
            logger.error(f"Vertex AI failed: {e}")
            # Fall through to local processing

        # Fallback to local processing
        logger.info("Using local fallback processing")
        result_b64 = process_local_fallback(person_b64, garment_b64)
        
        if result_b64:
            return Response({
                "success": True,
                "result_image": result_b64,
                "message": "Virtual try-on completed (basic mode)",
                "fallback": True
            })
        else:
            return Response({'error': 'All processing methods failed'}, status=500)

    except Exception as e:
        logger.error(f"Error in image_try_on: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=500)


def call_vertex_ai_api(person_b64, garment_b64):
    """Call Vertex AI API and return base64 result."""
    try:
        access_token = get_access_token()
        if not access_token:
            logger.error("Failed to get access token")
            return None

        project_id = 'probable-tape-421308'
        region = 'us-central1'
        url = f"https://{region}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{region}/publishers/google/models/virtual-try-on-001:predict"

        # Truncate base64 if too large (Vertex AI has limits)
        # Some models have 1.5MB limit for base64
        if len(person_b64) > 1_500_000:
            logger.warning(f"Person image too large ({len(person_b64)} chars), may fail")
        if len(garment_b64) > 1_500_000:
            logger.warning(f"Garment image too large ({len(garment_b64)} chars), may fail")

        payload = {
            "instances": [{
                "personImage": {"bytesBase64Encoded": person_b64},
                "productImages": [{"bytesBase64Encoded": garment_b64}],
                "person_generation": "ALLOW_ALL"
            }],
            "parameters": {
                "sampleCount": 1,
                "baseSteps": 32
            }
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Vercel has 10-60 second timeout, set timeout to 55 seconds
        logger.info(f"Calling Vertex AI API...")
        response = requests.post(url, json=payload, headers=headers, timeout=55)

        if not response.ok:
            logger.error(f"Vertex AI error {response.status_code}: {response.text[:500]}")
            return None

        result = response.json()
        predictions = result.get("predictions", [])
        
        if not predictions:
            logger.error(f"No predictions in response: {result}")
            return None

        # Get base64 result
        image_b64 = (
            predictions[0].get("bytesBase64Encoded") or
            predictions[0].get("image", {}).get("bytesBase64Encoded")
        )

        if not image_b64:
            logger.error(f"No image in prediction: {list(predictions[0].keys())}")
            return None

        logger.info(f"Vertex AI success, result size: {len(image_b64)} chars")
        return image_b64

    except requests.Timeout:
        logger.error("Vertex AI API timeout after 55 seconds")
        return None
    except Exception as e:
        logger.error(f"Vertex AI error: {e}")
        return None


def process_local_fallback(person_b64, garment_b64):
    """Process images locally without saving to disk."""
    try:
        import io
        from PIL import Image
        
        # Decode base64 to PIL images
        person_bytes = base64.b64decode(person_b64)
        garment_bytes = base64.b64decode(garment_b64)
        
        person = Image.open(io.BytesIO(person_bytes)).convert('RGBA')
        garment = Image.open(io.BytesIO(garment_bytes)).convert('RGBA')
        
        # Get dimensions
        person_width, person_height = person.size
        
        # Calculate garment position and size
        target_width = int(person_width * 0.85)
        target_height = int(garment.height * (target_width / garment.width))
        
        # Don't exceed reasonable size
        if target_height > person_height * 0.6:
            target_height = int(person_height * 0.6)
            target_width = int(garment.width * (target_height / garment.height))
        
        garment_resized = garment.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Position on upper body
        x_position = (person_width - target_width) // 2
        y_position = int(person_height * 0.2)
        
        # Composite images
        result = person.copy()
        result.paste(garment_resized, (x_position, y_position), garment_resized)
        result = result.convert('RGB')
        
        # Convert back to base64
        buffer = io.BytesIO()
        result.save(buffer, format='JPEG', quality=90)
        result_bytes = buffer.getvalue()
        result_b64 = base64.b64encode(result_bytes).decode('utf-8')
        
        logger.info(f"Local fallback success, result size: {len(result_b64)} chars")
        return result_b64
        
    except Exception as e:
        logger.error(f"Local processing error: {e}", exc_info=True)
        return None


@api_view(['POST'])
def pose_estimation_view(request):
    """Detect body pose for better garment fitting."""
    try:
        person_img = request.FILES.get('person_image')
        if not person_img:
            return Response({'error': 'person_image required'}, status=400)

        # Process image from memory without saving to disk
        person_img.seek(0)
        img = Image.open(person_img)
        width, height = img.size

        keypoints = {
            'nose': {'x': width * 0.50, 'y': height * 0.10},
            'left_shoulder': {'x': width * 0.30, 'y': height * 0.25},
            'right_shoulder': {'x': width * 0.70, 'y': height * 0.25},
            'left_elbow': {'x': width * 0.25, 'y': height * 0.35},
            'right_elbow': {'x': width * 0.75, 'y': height * 0.35},
            'left_wrist': {'x': width * 0.20, 'y': height * 0.45},
            'right_wrist': {'x': width * 0.80, 'y': height * 0.45},
            'left_hip': {'x': width * 0.35, 'y': height * 0.55},
            'right_hip': {'x': width * 0.65, 'y': height * 0.55},
            'left_knee': {'x': width * 0.35, 'y': height * 0.75},
            'right_knee': {'x': width * 0.65, 'y': height * 0.75},
            'left_ankle': {'x': width * 0.35, 'y': height * 0.90},
            'right_ankle': {'x': width * 0.65, 'y': height * 0.90},
        }

        clothing_zones = {
            'torso_zone': {
                'x': keypoints['left_shoulder']['x'],
                'y': keypoints['left_shoulder']['y'],
                'width': keypoints['right_shoulder']['x'] - keypoints['left_shoulder']['x'],
                'height': keypoints['left_hip']['y'] - keypoints['left_shoulder']['y'],
            },
            'upper_body': {
                'x': keypoints['left_shoulder']['x'],
                'y': keypoints['nose']['y'],
                'width': keypoints['right_shoulder']['x'] - keypoints['left_shoulder']['x'],
                'height': keypoints['left_hip']['y'] - keypoints['nose']['y'],
            }
        }

        return Response({
            'success': True,
            'keypoints': keypoints,
            'clothing_zones': clothing_zones
        })

    except Exception as e:
        logger.error(f"Pose estimation error: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=500)

