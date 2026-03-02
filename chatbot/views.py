from django.http import JsonResponse
from .services import get_shopping_response
import json
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def chat_endpoint(request):  
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "")
            bot_response = get_shopping_response(user_message)
            return JsonResponse({"response": bot_response})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Only POST requests allowed"}, status=405)