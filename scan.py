from processor import process_pdf_image
from config import INPUT_DIR, OUTPUT_PNG_DIR, OUTPUT_JSON_DIR, INPUT_PNG_DIR, MIN_AREA, MAX_AREA
import os
from pdf2image import convert_from_path
import json


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
        pdf_json_data = []  # Список для хранения JSON данных каждого файла
        for page_num, page in enumerate(pages, start=1):
            page_filename = f"{page_num}_{os.path.splitext(pdf_file)[0]}.png"  # Сохранение как png
            page_image_path = os.path.join(INPUT_PNG_DIR, page_filename)
            page.save(page_image_path, 'PNG')  # сохранение как png

            # Обработка и разметка pdf (по картинкам)
            json_data = process_pdf_image(page_image_path, page_num, os.path.splitext(pdf_file)[0], min_area=MIN_AREA, max_area=MAX_AREA)
            pdf_json_data.append(json_data)  # Сохраняем данные для каждой страницы

        # После обработки всех страниц, сохраняем данные JSON для всего PDF
        result_json_filename = os.path.join(OUTPUT_JSON_DIR, f"res_{os.path.splitext(pdf_file)[0]}.json")
        with open(result_json_filename, 'w') as result_json_file:
            json.dump(pdf_json_data, result_json_file, indent=4)

        # Отметка обработанного файла
        processed_files.append(pdf_file)
        print(f"Обработка завершена для файла {pdf_file}.")

print("Все файлы обработаны.")
