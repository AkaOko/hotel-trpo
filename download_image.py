import requests
import os

def download_image(url, save_path):
    try:
        # Создаем директорию, если она не существует
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Скачиваем изображение
        response = requests.get(url)
        response.raise_for_status()  # Проверяем на ошибки
        
        # Сохраняем изображение
        with open(save_path, 'wb') as f:
            f.write(response.content)
            
        print(f"Изображение успешно скачано и сохранено в {save_path}")
        return True
    except Exception as e:
        print(f"Ошибка при скачивании изображения: {str(e)}")
        return False

# URL изображения и путь для сохранения
image_url = "https://images.unsplash.com/photo-1631049307264-da0ec9d70304"
save_path = "static/images/room-default.jpg"

# Скачиваем изображение
download_image(image_url, save_path) 