import random
import numpy as np
import os
import json
import cv2
import pytesseract
import matplotlib.pyplot as plt
from processor.image_processing import enhance_image
from config import OUTPUT_PNG_DIR, OUTPUT_JSON_DIR, INPUT_PNG_DIR

# Укажите путь к Tesseract (если он не установлен глобально)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Для Windows

# Функция для генерации палитры контрастных цветов
def generate_color_palette():
    colors = []
    for _ in range(12):
        r = random.randint(50, 200)
        g = random.randint(50, 200)
        b = random.randint(50, 200)
        colors.append((r, g, b))
    return colors

# Функция для сохранения изображения с использованием matplotlib (в формате PNG)
def save_image_with_matplotlib(image, output_image_path):
    plt.figure(figsize=(10, 10))
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    plt.savefig(output_image_path, format='png', bbox_inches='tight', pad_inches=0)

# Функция для сохранения JSON
def save_json_data(json_data, output_image_name, pdf_filename):
    output_json_dir = os.path.join(OUTPUT_JSON_DIR, pdf_filename)
    os.makedirs(output_json_dir, exist_ok=True)  # Создаем поддиректорию для PDF
    json_filename = os.path.join(output_json_dir, f"{output_image_name}.json")
    with open(json_filename, 'w', encoding='utf-8') as json_file:
        json.dump(json_data, json_file, ensure_ascii=False, indent=4)

# Функция для подсчета статистики для каждого контура
def calculate_figure_stats(figure, enhanced_image):
    mask = np.zeros_like(enhanced_image)
    cv2.drawContours(mask, [figure], -1, 255, thickness=cv2.FILLED)

    figure_area = cv2.contourArea(figure)
    white_pixels = cv2.countNonZero(cv2.bitwise_and(enhanced_image, enhanced_image, mask=mask))
    black_pixels = np.count_nonzero(mask == 255) - white_pixels

    return figure_area, white_pixels, black_pixels

# Функция для извлечения текста из области
def extract_text_from_roi(image, contour):
    # Получаем ограничивающий прямоугольник
    x, y, w, h = cv2.boundingRect(contour)
    roi = image[y:y+h, x:x+w]  # Вырезаем область
    # Применяем OCR для распознавания текста
    text = pytesseract.image_to_string(roi, config='--psm 6', lang='rus')
    return text.strip()

# Функция для обработки изображения PDF и сохранения результатов
def process_pdf_image(image_path, page_num, pdf_filename, min_area, max_area):
    # Загрузка изображения и улучшение (черно-белая бинаризация)
    image = cv2.imread(image_path)
    enhanced_image = enhance_image(image)

    # Создаем копию улучшенного изображения для рисования цветных контуров
    colored_image = cv2.cvtColor(enhanced_image, cv2.COLOR_GRAY2BGR)  # Преобразуем в цветное для рисования

    # Поиск контуров на улучшенном изображении
    contours, _ = cv2.findContours(enhanced_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    json_data = {'fileName': f"o_{page_num}_{pdf_filename}.svg", 'matrix': {}, 'obj': []}
    colors = generate_color_palette()

    # Матрица для сегментации
    height, width = enhanced_image.shape
    section_width = width // 3
    levels = []
    level_threshold = 50

    matrix = {}

    # Обработка найденных контуров
    for idx, contour in enumerate(contours, start=1):
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # Отбираем прямоугольники (контуры с 4 углами)
        if len(approx) == 4:
            area = cv2.contourArea(contour)
            if min_area < area < max_area:
                figure_area, white_pix, black_pix = calculate_figure_stats(approx, enhanced_image)
                json_data['obj'].append({
                    'obj_num': idx,
                    'figure_area': figure_area,
                    'figure_white_pix': white_pix,
                    'figure_black_pix': black_pix
                })

                # Извлечение текста из области прямоугольника
                text = extract_text_from_roi(image, approx)
                if text:
                    json_data['obj'][-1]['text'] = text

                # Добавляем координаты углов (преобразуем в тип int)
                corners = [(int(pt[0][0]), int(pt[0][1])) for pt in approx]  # Преобразуем в тип int
                json_data['obj'][-1]['corners'] = corners  # Добавляем в json_data

                # Распределение по уровням (сегментация)
                moments = cv2.moments(approx)
                if moments["m00"] != 0:
                    center_x = int(moments["m10"] / moments["m00"])
                    center_y = int(moments["m01"] / moments["m00"])

                    section_idx = center_x // section_width
                    assigned = False
                    for level in levels:
                        if abs(center_y - level[0][1]) < level_threshold:
                            level.append((idx, center_y))
                            assigned = True
                            break

                    if not assigned:
                        level_label = f"s{len(levels) + 1}"
                        levels.append([(idx, center_y)])
                        matrix[level_label] = [''] * 3

                    # Раскрашивание контуров на копии улучшенного изображения
                    color = colors[idx % len(colors)]
                    cv2.drawContours(colored_image, [approx], -1, color, 2)
                    label_position = (center_x - 10, center_y - 10 if idx % 2 == 0 else center_y + 10)
                    cv2.putText(colored_image, str(idx), label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                    # Обновляем матрицу для секций
                    matrix[level_label][section_idx] += f"{idx} "

    json_data['matrix'] = matrix

    # Создаем поддиректорию для PDF в output_png
    output_png_dir = os.path.join(OUTPUT_PNG_DIR, pdf_filename)
    os.makedirs(output_png_dir, exist_ok=True)  # Создаем поддиректорию для PDF
    # Сохраняем изображение с цветными контурами
    save_image_with_matplotlib(colored_image, os.path.join(output_png_dir, f"colored_{page_num}_{pdf_filename}.png"))

    # Сохраняем JSON с данными
    save_json_data(json_data, f"o_{page_num}_{pdf_filename}", pdf_filename)

    return json_data

def visualize_all_images(all_colored_images):
    num_images = len(all_colored_images)

    fig, axes = plt.subplots(1, num_images, figsize=(15, 5))
    if num_images == 1:
        axes = [axes]

    for ax, image, idx in zip(axes, all_colored_images, range(num_images)):
        ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        ax.axis('off')
        ax.set_title(f"Image {idx + 1}")

    plt.show()
