import os
import csv
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings') # Просто settings
django.setup()

from api.models import Product

def run_import():
    with open('products.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Безопасно обрабатываем числа
            raw_year = row.get('year', '')
            year_val = int(float(raw_year)) if raw_year and raw_year.strip() else 0
            
            raw_price = row.get('price', '')
            price_val = float(raw_price) if raw_price and raw_price.strip() else 0.0

            Product.objects.get_or_create(
                product_id=int(float(row['id'])),
                defaults={
                    'filename': row['filename'],
                    'link': row['link'],
                    'gender': row['gender'],
                    'season': row['season'],
                    'year': year_val,           # Используем безопасное значение
                    'usage': row['usage'],
                    'master_category': row['masterCategory'],
                    'sub_category': row['subCategory'],
                    'article_type': row['articleType'],
                    'color': row['color'],
                    'price': price_val,         # Используем безопасное значение
                    'brand': row['brand'],
                    'silhouette': row.get('Silhouette', ''),
                    'figure': row.get('figure', ''),
                    'product_display_name': row['productDisplayName']
                }
            )
    print("Import finished successfully!")

if __name__ == "__main__":
    run_import()