# processor/file_management.py
import random
import numpy as np
import os
import json
import cv2
import matplotlib.pyplot as plt
from processor.contour_analysis import process_contours
from processor.image_processing import enhance_image
from config import OUTPUT_PNG_DIR, OUTPUT_JSON_DIR


# Функция для генерации палитры контрастных цветов
def generate_color_palette():
    colors = []
    for _ in range(12):
        r = random.randint(50, 200)
        g = random.randint(50, 200)
        b = random.randint(50, 200)
        colors.append((r, g, b))
    return colors


# Функция для сохранения изображения с использованием matplotlib (в формате SVG)
def save_image_with_matplotlib(image, output_image_path):
    plt.figure(figsize=(10, 10))
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    plt.savefig(output_image_path, format='svg', bbox_inches='tight', pad_inches=0)


# Функция для сохранения JSON
def save_json_data(json_data, output_image_name):
    json_filename = os.path.join(OUTPUT_JSON_DIR, f"{output_image_name}.json")
    with open(json_filename, 'w') as json_file:
        json.dump(json_data, json_file, indent=4)


# Функция для подсчета статистики для каждого контура
def calculate_figure_stats(figure, enhanced_image):
    """Перемещаем функцию сюда, чтобы избежать кругового импорта."""
    mask = np.zeros_like(enhanced_image)
    cv2.drawContours(mask, [figure], -1, 255, thickness=cv2.FILLED)

    figure_area = cv2.contourArea(figure)
    white_pixels = cv2.countNonZero(cv2.bitwise_and(enhanced_image, enhanced_image, mask=mask))
    black_pixels = np.count_nonzero(mask == 255) - white_pixels

    return figure_area, white_pixels, black_pixels


# Функция для обработки изображения PDF и сохранения результатов
def process_pdf_image(image_path, page_num, pdf_filename, min_area, max_area):
    # Перемещаем импорт сюда, чтобы избежать импорта в начале
    from processor.contour_analysis import calculate_figure_stats  # Отложенный импорт

    rectangles, enhanced_image = process_contours(image_path, min_area, max_area)

    json_data = {'fileName': f"o_{page_num}_{pdf_filename}.svg", 'obj': []}

    for rect, area, idx in rectangles:
        figure_area, white_pix, black_pix = calculate_figure_stats(rect, enhanced_image)
        json_data['obj'].append({
            'obj_num': idx,
            'figure_area': figure_area,
            'figure_white_pix': white_pix,
            'figure_black_pix': black_pix
        })

    # Сохраняем обработанное изображение в формате SVG
    save_image_with_matplotlib(enhanced_image, os.path.join(OUTPUT_PNG_DIR, f"processed_{page_num}_{pdf_filename}.svg"))

    # Генерация палитры цветов
    colors = generate_color_palette()

    # Применяем раскраску
    output_image = cv2.cvtColor(enhanced_image, cv2.COLOR_GRAY2BGR)

    for rect, area, idx in rectangles:
        color = colors[idx % len(colors)]  # Получаем цвет из палитры
        cv2.drawContours(output_image, [rect], -1, color, 2)
        moments = cv2.moments(rect)
        if moments["m00"] != 0:
            center_x = int(moments["m10"] / moments["m00"])
            center_y = int(moments["m01"] / moments["m00"])
            label_position = (center_x - 10, center_y - 10 if idx % 2 == 0 else center_y + 10)
            cv2.putText(output_image, str(idx), label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # Сохраняем финальное раскрашенное изображение
    save_image_with_matplotlib(output_image, os.path.join(OUTPUT_PNG_DIR, f"colored_{page_num}_{pdf_filename}.svg"))

    # Сохраняем JSON данные
    save_json_data(json_data, f"o_{page_num}_{pdf_filename}")

    return output_image  # Возвращаем раскрашенное изображение для последующей визуализации


def visualize_all_images(all_colored_images):
    num_images = len(all_colored_images)

    # Создаем подгруппы для отображения всех изображений
    fig, axes = plt.subplots(1, num_images, figsize=(15, 5))
    if num_images == 1:
        axes = [axes]  # Для случая, если изображение одно, чтобы axes был iterable

    # Отображаем каждое изображение
    for ax, image, idx in zip(axes, all_colored_images, range(num_images)):
        ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        ax.axis('off')  # Отключаем оси
        ax.set_title(f"Image {idx + 1}")

    plt.show()