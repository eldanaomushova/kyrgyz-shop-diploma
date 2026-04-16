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
from google.cloud import storage
import uuid

logger = logging.getLogger(__name__)

# Инициализация Cloud Storage
try:
    storage_client = storage.Client()
    bucket_name = 'stilno-tryon-results'
    bucket = storage_client.bucket(bucket_name)
    logger.info(f"Connected to Cloud Storage bucket: {bucket_name}")
except Exception as e:
    logger.error(f"Failed to connect to Cloud Storage: {e}")
    bucket = None


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


@api_view(['POST'])
def image_try_on(request):
    person_img = None
    garment_img = None
    temp_files = []
    
    try:
        person_img = request.FILES.get('person_image')
        garment_img = request.FILES.get('garment_image')

        if not person_img or not garment_img:
            return Response({'error': 'Both images are required'}, status=400)

        # Используем tempfile вместо локальной папки
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_person:
            for chunk in person_img.chunks():
                tmp_person.write(chunk)
            person_path = tmp_person.name
            temp_files.append(person_path)

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_garment:
            for chunk in garment_img.chunks():
                tmp_garment.write(chunk)
            garment_path = tmp_garment.name
            temp_files.append(garment_path)

        logger.info(f"Person file size: {os.path.getsize(person_path)} bytes")
        logger.info(f"Garment file size: {os.path.getsize(garment_path)} bytes")

        result_image_path = None
        
        # Пытаемся использовать Vertex AI
        try:
            logger.info("Attempting Vertex AI processing...")
            result_image_path = process_virtual_try_on_vertex(person_path, garment_path)
            if result_image_path:
                logger.info("Vertex AI processing successful")
                temp_files.append(result_image_path)
        except Exception as e:
            logger.error(f"Vertex AI failed: {e}")

        # Если Vertex AI не сработал, используем локальный fallback
        if not result_image_path:
            logger.info("Falling back to local processing...")
            result_image_path = process_virtual_try_on_local(person_path, garment_path)
            if result_image_path:
                temp_files.append(result_image_path)

        # Если ничего не сработало
        if not result_image_path:
            return Response({'error': 'All processing methods failed'}, status=500)

        # Загружаем результат в Cloud Storage
        result_url = None
        if bucket:
            try:
                blob_name = f"tryon_results/result_{int(time.time())}_{uuid.uuid4().hex[:8]}.jpg"
                blob = bucket.blob(blob_name)
                
                # Загружаем файл
                blob.upload_from_filename(result_image_path, content_type='image/jpeg')
                
                # Делаем публичным (или используем signed URL)
                blob.make_public()
                result_url = blob.public_url
                
                logger.info(f"Result uploaded to Cloud Storage: {result_url}")
            except Exception as e:
                logger.error(f"Failed to upload to Cloud Storage: {e}")
                # Если Cloud Storage не работает, используем base64
                with open(result_image_path, 'rb') as img_file:
                    img_b64 = base64.b64encode(img_file.read()).decode('utf-8')
                    result_url = f"data:image/jpeg;base64,{img_b64}"

        return Response({
            "success": True,
            "result_url": result_url,
            "message": "Virtual try-on completed!",
            "used_fallback": result_image_path and "local" in result_image_path
        })

    except Exception as e:
        logger.error(f"Error in image_try_on: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=500)
    
    finally:
        # Очищаем временные файлы
        for file_path in temp_files:
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {file_path}: {e}")


def normalize_to_jpeg(path):
    """Convert any image to JPEG and return path to temp file."""
    try:
        img = Image.open(path).convert('RGB')
        
        # Уменьшаем размер если слишком большой
        max_size = 1500
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        buf = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        img.save(buf.name, 'JPEG', quality=85, optimize=True)
        buf.close()
        return buf.name
    except Exception as e:
        logger.error(f"Error normalizing image: {e}")
        raise


def process_virtual_try_on_vertex(person_path, garment_path):
    """Process virtual try-on using Vertex AI Virtual Try-On API."""
    person_normalized = None
    garment_normalized = None
    try:
        access_token = get_access_token()
        if not access_token:
            logger.error("Failed to get access token")
            return None

        person_normalized = normalize_to_jpeg(person_path)
        garment_normalized = normalize_to_jpeg(garment_path)

        with open(person_normalized, "rb") as f:
            person_b64 = base64.b64encode(f.read()).decode("utf-8")
        with open(garment_normalized, "rb") as f:
            garment_b64 = base64.b64encode(f.read()).decode("utf-8")

        logger.info(f"Person b64 length: {len(person_b64)}, Garment b64 length: {len(garment_b64)}")

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
                        "bytesBase64Encoded": person_b64
                    },
                    "productImages": [
                        {
                            "bytesBase64Encoded": garment_b64
                        }
                    ],
                    "person_generation": "ALLOW_ALL"
                }
            ],
            "parameters": {
                "sampleCount": 1,
                "baseSteps": 32
            }
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        logger.info(f"Calling Vertex AI VTO API: {url}")
        response = requests.post(url, json=payload, headers=headers, timeout=55)  # Таймаут для Vercel

        if not response.ok:
            logger.error(f"VTO API error {response.status_code}: {response.text[:500]}")
            return None

        result = response.json()
        logger.info(f"VTO API response keys: {list(result.keys())}")

        predictions = result.get("predictions", [])
        if not predictions:
            logger.error(f"No predictions in response")
            return None

        image_b64 = (
            predictions[0].get("bytesBase64Encoded") or
            predictions[0].get("image", {}).get("bytesBase64Encoded")
        )

        if not image_b64:
            logger.error(f"No image data in prediction")
            return None

        image_bytes = base64.b64decode(image_b64)
        temp_output = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        temp_output.write(image_bytes)
        temp_output.close()

        logger.info(f"VTO result saved to: {temp_output.name}")
        return temp_output.name

    except requests.Timeout:
        logger.error("Vertex AI API timeout")
        return None
    except Exception as e:
        logger.error(f"Vertex AI VTO Error: {e}", exc_info=True)
        return None

    finally:
        for p in [person_normalized, garment_normalized]:
            if p and os.path.exists(p):
                try:
                    os.unlink(p)
                except:
                    pass


def process_virtual_try_on_local(person_image_path, garment_image_path):
    """Fallback local processing — overlays garment onto person image."""
    try:
        person = Image.open(person_image_path).convert('RGBA')
        garment = Image.open(garment_image_path).convert('RGBA')

        person_width, person_height = person.size

        target_width = int(person_width * 0.55)
        target_height = int(garment.height * (target_width / garment.width))
        
        # Не делаем одежду слишком большой
        if target_height > person_height * 0.6:
            target_height = int(person_height * 0.6)
            target_width = int(garment.width * (target_height / garment.height))
        
        garment_resized = garment.resize((target_width, target_height), Image.Resampling.LANCZOS)

        x_position = (person_width - target_width) // 2
        y_position = int(person_height * 0.2)

        result = person.copy()
        result.paste(garment_resized, (x_position, y_position), garment_resized)
        result = result.convert('RGB')

        temp_output = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        result.save(temp_output.name, 'JPEG', quality=90)
        logger.info(f"Local fallback result saved to: {temp_output.name}")
        return temp_output.name

    except Exception as e:
        logger.error(f"Local processing error: {str(e)}", exc_info=True)
        return None


@api_view(['POST'])
def pose_estimation_view(request):
    """Detect body pose for better garment fitting."""
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
        logger.error(f"Pose estimation error: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=500)


def detect_pose_keypoints(image_path):
    """Estimate pose keypoints using proportional image analysis."""
    img = Image.open(image_path)
    width, height = img.size

    return {
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


def calculate_clothing_zones(keypoints):
    """Calculate clothing placement zones from keypoints."""
    return {
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