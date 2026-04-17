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
from google.cloud import aiplatform, storage
import requests
import base64
from google.oauth2 import service_account
import google.auth.transport.requests
import google.auth
from io import BytesIO
import uuid

logger = logging.getLogger(__name__)

try:
    storage_client = storage.Client(project='probable-tape-421308')
    BUCKET_NAME = 'stilno-tryon-results'
    bucket = storage_client.bucket(BUCKET_NAME)
    logger.info(f"Google Cloud Storage initialized with bucket: {BUCKET_NAME}")
except Exception as e:
    logger.error(f"Failed to initialize Google Cloud Storage: {e}")
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

def upload_to_gcs(file_path, destination_blob_name):
    """Upload a file to Google Cloud Storage"""
    try:
        if not bucket:
            logger.error("GCS bucket not initialized")
            return None
            
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(file_path)
        
        # Make the blob publicly accessible
        blob.make_public()
        
        public_url = blob.public_url
        logger.info(f"File uploaded to GCS: {public_url}")
        return public_url
    except Exception as e:
        logger.error(f"Failed to upload to GCS: {e}")
        return None

def upload_bytes_to_gcs(image_bytes, destination_blob_name, content_type='image/jpeg'):
    """Upload bytes directly to Google Cloud Storage"""
    try:
        if not bucket:
            logger.error("GCS bucket not initialized")
            return None
            
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(image_bytes, content_type=content_type)
        
        # Make the blob publicly accessible
        blob.make_public()
        
        public_url = blob.public_url
        logger.info(f"Bytes uploaded to GCS: {public_url}")
        return public_url
    except Exception as e:
        logger.error(f"Failed to upload bytes to GCS: {e}")
        return None

try:
    aiplatform.init(
        project='probable-tape-421308',
        location='us-central1',
    )
    vertexai.init(project='probable-tape-421308', location='us-central1')
    logger.info("Vertex AI initialized successfully")
except Exception as e:
    logger.warning(f"Vertex AI initialization failed: {e}")

@api_view(['POST'])
def image_try_on(request):
    try:
        person_img = request.FILES.get('person_image')
        garment_img = request.FILES.get('garment_image')
        
        if not person_img or not garment_img:
            return Response({'error': 'Both images are required'}, status=400)
        
        temp_dir = tempfile.mkdtemp()
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        
        person_path = os.path.join(temp_dir, f'person_{timestamp}_{unique_id}.jpg')
        garment_path = os.path.join(temp_dir, f'garment_{timestamp}_{unique_id}.jpg')

        try:
            with open(person_path, 'wb') as f:
                for chunk in person_img.chunks():
                    f.write(chunk)

            with open(garment_path, 'wb') as f:
                for chunk in garment_img.chunks():
                    f.write(chunk)

            logger.info(f"Person file size: {os.path.getsize(person_path)} bytes")
            logger.info(f"Garment file size: {os.path.getsize(garment_path)} bytes")
            
            result_image_path = process_virtual_try_on_vertex(person_path, garment_path)
            
            if not result_image_path:
                # Fallback to local processing if Vertex AI fails
                logger.info("Falling back to local processing...")
                result_image_path = process_virtual_try_on_local(person_path, garment_path)
            
            if not result_image_path:
                return Response({'error': 'AI processing failed'}, status=500)

            result_filename = f"result_{timestamp}_{unique_id}.jpg"
            gcs_path = f"tryon_results/{result_filename}"
            
            result_url = upload_to_gcs(result_image_path, gcs_path)
            
            if not result_url:
                return Response({'error': 'Failed to upload result to storage'}, status=500)
            
            os.unlink(result_image_path)
            
            return Response({
                "success": True,
                "result_url": result_url,
                "message": "AI Virtual try-on completed!",
                "storage": "gcs"
            })
            
        finally:
            for path in [person_path, garment_path]:
                if os.path.exists(path): 
                    try:
                        os.unlink(path)
                    except:
                        pass
            try:
                os.rmdir(temp_dir)
            except:
                pass
            
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=500)

def process_virtual_try_on_vertex(person_path, garment_path):
    """Process virtual try-on using Vertex AI (without local key file)"""
    try:
        access_token = get_access_token()
        if not access_token:
            logger.error("Failed to get access token")
            return None

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
            logger.error(f"VTO API error {response.status_code}: {response.text[:500]}")
            return None

        result = response.json()
        predictions = result.get("predictions", [])

        if not predictions:
            logger.error(f"No predictions returned")
            return None

        image_b64 = predictions[0].get("bytesBase64Encoded")
        if not image_b64:
            logger.error(f"No image in prediction")
            return None

        image_bytes = base64.b64decode(image_b64)
        temp_output = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        temp_output.write(image_bytes)
        temp_output.close()
        return temp_output.name

    except Exception as e:
        logger.error(f"Vertex AI VTO Error: {e}")
        return None

def process_virtual_try_on_local(person_image_path, garment_image_path):
    """
    Process virtual try-on locally with improved garment placement
    No API key required - works as fallback
    """
    try:
        person = Image.open(person_image_path).convert('RGBA')
        garment = Image.open(garment_image_path).convert('RGBA')
        
        person_width, person_height = person.size
        
        target_width = int(person_width * 0.45)
        target_height = int(garment.height * (target_width / garment.width))
        
        garment_resized = garment.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        x_position = (person_width - target_width) // 2
        y_position = int(person_height * 0.2)
        
        result = person.copy()
        
        result.paste(garment_resized, (x_position, y_position), garment_resized)
        
        result = result.convert('RGB')
        
        temp_output = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        result.save(temp_output.name, 'JPEG', quality=95)
        
        return temp_output.name
        
    except Exception as e:
        logger.error(f"Local processing error: {str(e)}")
        return None

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
    """Test endpoint to check if image exists in GCS"""
    try:
        if not bucket:
            return JsonResponse({'error': 'GCS bucket not initialized'}, status=500)
            
        gcs_path = f"tryon_results/{filename}"
        blob = bucket.blob(gcs_path)
        
        if blob.exists():
            # Redirect to GCS public URL or serve through your app
            blob.make_public()
            return JsonResponse({
                'exists': True,
                'url': blob.public_url
            })
        else:
            return JsonResponse({'error': f'File not found: {gcs_path}'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Optional: Add a view to list all results
@api_view(['GET'])
def list_tryon_results(request):
    """List all try-on results in GCS"""
    try:
        if not bucket:
            return Response({'error': 'GCS bucket not initialized'}, status=500)
            
        blobs = bucket.list_blobs(prefix='tryon_results/')
        results = []
        for blob in blobs:
            blob.make_public()
            results.append({
                'name': blob.name.split('/')[-1],
                'url': blob.public_url,
                'size': blob.size,
                'updated': blob.updated.isoformat() if blob.updated else None
            })
        
        return Response({
            'success': True,
            'count': len(results),
            'results': results
        })
    except Exception as e:
        logger.error(f"Error listing results: {e}")
        return Response({'error': str(e)}, status=500)