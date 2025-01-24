# processor/contour_analysis.py
import cv2
from processor.image_processing import enhance_image
import numpy as np


def process_contours(image_path, min_area, max_area):
    """Поиск контуров на изображении."""
    image = cv2.imread(image_path)
    enhanced_image = enhance_image(image)  # вызываем функцию из image_processing.py

    contours, _ = cv2.findContours(enhanced_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    rectangles = []
    for i, contour in enumerate(contours, start=1):
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        if len(approx) == 4:  # Только прямоугольники
            area = cv2.contourArea(contour)
            if min_area < area < max_area:
                rectangles.append((approx, area, i))

    return rectangles, enhanced_image


def calculate_figure_stats(figure, enhanced_image):
    """Подсчет статистики для каждого контура."""
    mask = np.zeros_like(enhanced_image)
    cv2.drawContours(mask, [figure], -1, 255, thickness=cv2.FILLED)

    figure_area = cv2.contourArea(figure)
    white_pixels = cv2.countNonZero(cv2.bitwise_and(enhanced_image, enhanced_image, mask=mask))
    black_pixels = np.count_nonzero(mask == 255) - white_pixels

    return figure_area, white_pixels, black_pixels
