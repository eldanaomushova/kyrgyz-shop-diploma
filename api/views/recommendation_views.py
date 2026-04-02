import logging
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework import status
from django.db import models
from ..serializers import ProductSerializer  # ← исправлен импорт
from ..models import Product

logger = logging.getLogger(__name__)

ALLOWED_CATEGORIES = ['Кийим-кече', 'Бут кийим']
EXCLUDED_ARTICLE_TYPES = [
    'Дезодарант', 'Духи жана спрей', 'Духи топтому', 'Парфюмерия',
    'Шарф', 'Шарфтар', 'Галстук', 'Галстуктар', 'Ремень', 'Ремендер',
    'Көз айнек', 'Көз айнектер', 'Зергер буюмдары топтому', 'Зер буюмдардар',
    'Шурулар', 'Билериктер', 'Сөйкөлөр', 'Шакек', 'Браслет', 'Кулон',
    'Саат', 'Сааттар', 'Макияж', 'Тырмактар', 'Териге кам көрүү',
    'Дене жана ванна үчүн Каражаттар', 'Духи', 'Помада', 'Тушь',
    'Суу бытылка', 'Планшетке чехол', 'Чехол', 'Зонт', 'Зонттор',
    'Көйнөктөр', 'Зер буюмдардар', 'Клатч', 'Помада', 'Бюстгалтер'
]

OCCASION_MAPPING = {
    'casual': {
        'usage': 'Күн сайын',
        'article_types': ['Футболка', 'Джинсы', 'Шымдар', 'Шорты', 'Юбка', 
                        'Толстовка', 'Майка', 'Капри', 'Күнүмдүк бут кийим', 
                        'Сандалдар', 'Балетка', 'Шлепки']
    },
    'formal': {
        'usage': 'Формалдуу',
        'article_types': ['Костюм', 'Рубашка', 'Расмий бут кийим', 'Көйнөк', 
                        'Туфли', 'Жилетка']
    },
    'party': {
        'usage': 'Кече',
        'article_types': ['Көйнөк', 'Туфли', 'Юбка', 'Костюм', 'Балетка']
    },
    'sports': {
        'usage': 'Спорт',
        'article_types': ['Спорттук шымдар', 'Спорт бут кийим', 'Спорттук костюмдар',
                        'Толстовка', 'Шорты', 'Спорт Сандалдар', 'Футболка']
    },
    'travel': {
        'usage': 'Саякат',
        'article_types': ['Спорттук шымдар', 'Күнүмдүк бут кийим', 'Толстовка',
                        'Джинсы', 'Футболка', 'Сандалдар', 'Шорты']
    }
}

BODY_TYPE_MAPPING = {
    'slim': ['Slim Fit'],
    'regular': ['Regular Fit', 'Standard Fit', 'Fitted/Standard'],
    'athletic': ['Regular Fit', 'Slim Fit', 'Fitted/Standard'],
    'plus': ['Relaxed Fit', 'Comfort Fit'],
    'petite': ['Slim Fit', 'Regular Fit']
}

COLOR_MAPPING = {
    'black': ['Кара', 'Көмүр', 'Кара-Көк'], 
    'blue': ['Көк', 'Бирюзовый', 'Бирюза-көк', 'Кызгылт көк', 'Кара-Көк'],  
    'red': ['Кызыл', 'Бургундия', 'Роза'],
    'green': ['Жашыл', 'Хаки', 'Оливка', 'Лайм', 'Деңиз жашыл', 'Флуоресцент жашыл'], 
    'white': ['Ак', 'Серебро', 'Беж', 'Ак-кичине бос', 'Крем'], 
    'brown': ['Күрөң', 'Беж', 'Кофе күрөң', 'Ачык-Күрөң', 'Боз-күрөң', 'Грибной коричневый', 'Нюд', 'Тери', 'Ржавчина'], 
    'gray': ['Боз', 'Боз меланж', 'Күңүрт', 'Боз-күрөң', 'Серебро', 'Болот', 'Металдык'], 
    'yellow': ['Сары', 'Горчица', 'Жез', 'Алтын'],  
    'purple': ['Фиолетовый', 'Лаванда', 'Пурпурный'], 
    'pink': ['Кызгылт', 'Роза', 'Персик', 'Кызгылт көк'],  
    'multi': ['Көп түс'], 
    'orange': ['Персик', 'Ржавчина', 'Жез'], 
    'bronze': ['Бронза', 'Алтын', 'Металдык']  
}

@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def clothing_questionnaire(request):
    try:
        data = request.data
        occasion = data.get('occasion')
        body_type = data.get('body_type')
        preferred_colors = data.get('preferred_colors', [])
        budget = data.get('budget')
        gender = data.get('gender')
        
        if not all([occasion, body_type, gender]):
            missing_fields = []
            if not occasion: missing_fields.append('occasion')
            if not body_type: missing_fields.append('body_type')
            if not gender: missing_fields.append('gender')
            return Response(
                {'error': f'Missing required fields: {", ".join(missing_fields)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            query = Product.objects.all()
            query = query.filter(masterCategory__in=ALLOWED_CATEGORIES)
            query = query.exclude(articleType__in=EXCLUDED_ARTICLE_TYPES)
            
            if gender:
                query = query.filter(gender__iexact=gender)
            
            occasion_config = OCCASION_MAPPING.get(occasion, OCCASION_MAPPING.get('casual'))
            
            if occasion_config.get('usage'):
                query = query.filter(usage__iexact=occasion_config['usage'])
            if occasion_config.get('article_types'):
                query = query.filter(articleType__in=occasion_config['article_types'])
            
            # Body type filter
            if body_type and body_type in BODY_TYPE_MAPPING:
                silhouette_filter = BODY_TYPE_MAPPING[body_type]
                silhouette_condition = models.Q()
                for fit in silhouette_filter:
                    silhouette_condition |= models.Q(silhouette__icontains=fit)
                    silhouette_condition |= models.Q(figure__icontains=fit)
                if query.filter(silhouette_condition).exists():
                    query = query.filter(silhouette_condition)
            
            # Color filter
            if preferred_colors:
                color_condition = models.Q()
                for color in preferred_colors:
                    color_variants = COLOR_MAPPING.get(color.lower(), [color])
                    for variant in color_variants:
                        color_condition |= models.Q(color__iexact=variant)
                
                filtered = query.filter(color_condition)
                if filtered.exists():
                    query = filtered
                else:
                    logger.info(f"No products matched color filter, skipping color...")
            
            # Budget filter
            if budget:
                if budget == 'low':
                    query = query.filter(price__lte=2000)
                elif budget == 'medium':
                    query = query.filter(price__gte=2000, price__lte=5000)
                elif budget == 'high':
                    query = query.filter(price__gte=5000)
            
            recommended_products = query.order_by('?')[:10]
            
            if not recommended_products.exists():
                logger.warning(f"No products found for gender: {gender}, occasion: {occasion}")
                return Response({
                    'recommendations': [],
                    'recommendation_count': 0,
                    'message': 'No products match your criteria. Please try different preferences.',
                    'filters_applied': {
                        'occasion': occasion,
                        'body_type': body_type,
                        'preferred_colors': preferred_colors,
                        'budget': budget,
                        'gender': gender
                    }
                }, status=status.HTTP_200_OK)
            
            serializer = ProductSerializer(recommended_products, many=True)
            return Response({
                'recommendations': serializer.data,
                'recommendation_count': recommended_products.count(),
                'filters_applied': {
                    'occasion': occasion,
                    'body_type': body_type,
                    'preferred_colors': preferred_colors,
                    'budget': budget,
                    'gender': gender
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as db_error:
            logger.error(f"Database query error: {str(db_error)}", exc_info=True)
            return Response({
                'recommendations': [],
                'recommendation_count': 0,
                'error': 'Database query error',
                'message': str(db_error)
            }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Internal server error', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )