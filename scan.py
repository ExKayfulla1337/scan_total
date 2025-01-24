# scan.py
from processor import process_pdf_image, visualize_all_images
from config import INPUT_DIR, OUTPUT_PNG_DIR, OUTPUT_JSON_DIR, INPUT_PNG_DIR
import os
from pdf2image import convert_from_path

# Проверяем созданы ли папочки
os.makedirs(OUTPUT_PNG_DIR, exist_ok=True)
os.makedirs(OUTPUT_JSON_DIR, exist_ok=True)
os.makedirs(INPUT_PNG_DIR, exist_ok=True)

# Трекинг обработки файлов
processed_files = []
all_colored_images = []  # Список для хранения всех раскрашенных изображений

for pdf_file in os.listdir(INPUT_DIR):
    if pdf_file.endswith(".pdf"):
        # Пропускаем обработку обработанных pdf
        if pdf_file in processed_files:
            print(f"Файл: {pdf_file} уже был обработан, пропускаем.")
            continue

        print(f"Начинаем обработку: {pdf_file}")
        pdf_path = os.path.join(INPUT_DIR, pdf_file)
        pages = convert_from_path(pdf_path, dpi=150)

        # Обработка каждой pdf
        for page_num, page in enumerate(pages, start=1):
            page_filename = f"{page_num}_{os.path.splitext(pdf_file)[0]}.png"  # Сохранение как png
            page_image_path = os.path.join(INPUT_PNG_DIR, page_filename)
            page.save(page_image_path, 'PNG')  # сохранение как png

            # Обработка и разметка pdf (по картинкам)
            colored_image = process_pdf_image(page_image_path, page_num, os.path.splitext(pdf_file)[0], min_area=500, max_area=40000)
            all_colored_images.append(colored_image)  # Добавляем раскрашенное изображение в список

        # Отметка обработанного файла
        processed_files.append(pdf_file)
        print(f"Обработка завершена для файла {pdf_file}.")

# После обработки всех файлов, визуализируем все раскрашенные изображения
visualize_all_images(all_colored_images)

print("Все файлы обработаны.")
