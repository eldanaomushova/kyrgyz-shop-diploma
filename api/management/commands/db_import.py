import csv
from django.core.management.base import BaseCommand
from api.models import Product

class Command(BaseCommand):
    help = 'Imports products from products.csv'

    def handle(self, *args, **options):
        self.stdout.write("Clearing existing products...")
        Product.objects.all().delete()

        with open('products.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                raw_year = row.get('year', '')
                year_val = int(float(raw_year)) if raw_year and raw_year.strip() else 0
                
                raw_price = row.get('price', '')
                price_val = float(raw_price) if raw_price and raw_price.strip() else 0.0

                Product.objects.create(
                    product_id=int(float(row['id'])),
                    productDisplayName=row.get('productDisplayName', 'Unknown'),
                    link=row.get('link', ''),
                    gender=row.get('gender', ''),
                    season=row.get('season', ''),
                    year=year_val,
                    usage=row.get('usage', ''),
                    masterCategory=row.get('masterCategory', ''),
                    subCategory=row.get('subCategory', ''),
                    articleType=row.get('articleType', ''),
                    color=row.get('baseColour', ''),
                    price=price_val
                )
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} products!'))