import csv
import os
import sqlite3
import traceback

# Теперь используем файл базы данных, который создал Django
DB_FILE = 'db.sqlite3'

def import_products():
    csv_path = 'products.csv'
    
    if not os.path.exists(csv_path):
        print(f"❌ File not found: {csv_path}")
        return
    
    try:
        # Подключаемся к локальной базе SQLite
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        print("✅ Connected to SQLite Database")
        
        # Проверяем структуру таблицы в SQLite
        cursor.execute("PRAGMA table_info(api_product)")
        columns = cursor.fetchall()
        print("\n📋 Table structure:")
        for col in columns:
            print(f"   {col[1]} ({col[2]})")
        
        # Очищаем таблицу (В SQLite нет TRUNCATE, используем DELETE)
        cursor.execute("DELETE FROM api_product")
        # Сбрасываем автоинкремент счетчика ID
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='api_product'")
        conn.commit()
        print("\n✅ Cleared existing data")
        
        # Импортируем данные
        print(f"\n📂 Importing from {csv_path}")
        
        count = 0
        errors = []
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Обработка года
                    year_value = None
                    year_str = row.get('year', '').strip()
                    if year_str:
                        try:
                            year_value = int(float(year_str))
                        except:
                            pass
                    
                    # Обработка цены
                    price_value = 0.0
                    price_str = row.get('price', '').strip()
                    if price_str:
                        try:
                            price_value = float(price_str)
                        except:
                            pass
                    
                    # Обработка цвета
                    color_value = row.get('color', '').strip()
                    if not color_value:
                        color_value = None
                    
                    # Подготовка данных для вставки
                    data = (
                        int(row['id']),
                        row.get('productDisplayName', '')[:500],
                        row.get('masterCategory', '')[:100],
                        row.get('subCategory', '')[:100],
                        row.get('articleType', '')[:100],
                        row.get('filename', '')[:255],
                        row.get('link', '')[:500],
                        row.get('gender', '')[:50],
                        row.get('season', '')[:50] if row.get('season') else None,
                        year_value,
                        row.get('usage', '')[:100] if row.get('usage') else None,
                        color_value,
                        price_value,
                        row.get('brand', '')[:100] if row.get('brand') else None,
                        row.get('Silhouette') or None,
                        row.get('figure') or None,
                    )
                    
                    # Выполняем вставку (Заменили %s на ?)
                    cursor.execute('''
                        INSERT INTO api_product (
                            id, 
                            "productDisplayName", 
                            "masterCategory", 
                            "subCategory", 
                            "articleType",
                            filename, 
                            link, 
                            gender, 
                            season, 
                            year, 
                            usage, 
                            color, 
                            price, 
                            brand,
                            "Silhouette", 
                            figure
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', data)
                    count += 1
                    
                    if count % 1000 == 0:
                        conn.commit()
                        print(f"✅ Imported {count} products...")
                        
                except Exception as e:
                    error_msg = f"Row {row_num}: {str(e)}"
                    errors.append(error_msg)
                    print(f"❌ {error_msg}")
                    if count < 10:  
                        print(f"   Row data: {row}")
                    conn.rollback()
                    continue
            
            conn.commit()
        
        print(f"\n{'='*50}")
        print(f"IMPORT COMPLETED")
        print(f"{'='*50}")
        print(f"Total imported: {count} products")
        print(f"Errors: {len(errors)}")
        
        if errors:
            print(f"\nFirst 10 errors:")
            for error in errors[:10]:
                print(f"  - {error}")
        
        # Проверка общего количества
        cursor.execute("SELECT COUNT(*) FROM api_product")
        total = cursor.fetchone()[0]
        
        # Проверка заполненности цветов
        cursor.execute("SELECT COUNT(*) FROM api_product WHERE color IS NOT NULL AND color != ''")
        with_color = cursor.fetchone()[0]
        
        print(f"\n{'='*50}")
        print(f"VERIFICATION")
        print(f"{'='*50}")
        print(f"Total products in DB: {total}")
        if total > 0:
            print(f"With color: {with_color} ({with_color/total*100:.1f}%)")
        
        # Проверка цвета Боз
        cursor.execute("SELECT COUNT(*) FROM api_product WHERE color = 'Боз'")
        gray_count = cursor.fetchone()[0]
        print(f"Products with 'Боз': {gray_count}")
        
        # Примеры импортированных строк
        if total > 0:
            print(f"\n📝 Sample products:")
            cursor.execute("SELECT id, \"productDisplayName\", color, price FROM api_product LIMIT 5")
            for row in cursor.fetchall():
                print(f"  ID: {row[0]} | {row[1][:50]} | Color: '{row[2]}' | Price: {row[3]}")
            
            # Показываем уникальные цвета
            cursor.execute("""
                SELECT color, COUNT(*) 
                FROM api_product 
                WHERE color IS NOT NULL AND color != '' 
                GROUP BY color 
                ORDER BY COUNT(*) DESC 
                LIMIT 20
            """)
            colors = cursor.fetchall()
            if colors:
                print(f"\n🎨 Top colors:")
                for color in colors:
                    print(f"  '{color[0]}': {color[1]} products")
        
        cursor.close()
        conn.close()
        
        if total > 0:
            print(f"\n✅ Import successful! Now run:")
            print(f"   python manage.py runserver")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    import_products()