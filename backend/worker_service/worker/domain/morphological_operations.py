import numpy as np
import cv2
from enum import Enum
from worker.exceptions import ValidationError
from my_observability import get_logger

logger = get_logger(__name__)

class ImageType(Enum):
    BLACK_AND_WHITE = 1
    GREY_SCALE = 2
    COLOR = 3
    UNDEFINED = 4

class StructuringElementType(Enum):
    RECT = "rect"
    ELLIPSE = "ellipse"
    CROSS = "cross"

class OperationType(Enum):
    DILATE = "dilate"
    ERODE = "erode"
    OPENING = "opening"
    CLOSING = "closing"
    CONTOUR = "contour"
    TOP_HAT = "top_hat"
    BOTTOM_HAT = "bottom_hat"

def classify_image_array(image: np.ndarray) -> ImageType:
    if image.ndim == 2:
        unique = np.unique(image)
        if np.all(np.isin(unique, [0, 255])):
            return ImageType.BLACK_AND_WHITE
        return ImageType.GREY_SCALE
    
    if image.ndim == 3:
        if np.all(image[..., 0] == image[..., 1]) and np.all(image[..., 1] == image[..., 2]):
            return ImageType.GREY_SCALE
        return ImageType.COLOR
    
    return ImageType.UNDEFINED

def create_structuring_element(shape_type: str, size: tuple) -> np.ndarray:
    if shape_type == StructuringElementType.RECT.value:
        return cv2.getStructuringElement(cv2.MORPH_RECT, size)
    elif shape_type == StructuringElementType.ELLIPSE.value:
        return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, size)
    elif shape_type == StructuringElementType.CROSS.value:
        return cv2.getStructuringElement(cv2.MORPH_CROSS, size)
    else:
        raise ValueError("Invalid structuring element shape")

def execute_operation(operation: str, image: np.ndarray, struct_element: np.ndarray, image_type: ImageType) -> np.ndarray:
    OPERATIONS = {
        OperationType.DILATE.value: dilate,
        OperationType.ERODE.value: erode,
        OperationType.OPENING.value: opening,
        OperationType.CLOSING.value: closing,
        OperationType.CONTOUR.value: contour_extraction,
        OperationType.TOP_HAT.value: top_hat,
        OperationType.BOTTOM_HAT.value: bottom_hat
    }

    if operation not in OPERATIONS:
        logger.warning("Unsupported operation requested: %s", operation)
        raise ValidationError(f"Unsupported operation: {operation}")
    
    res =  OPERATIONS[operation](image, struct_element, image_type)

    if image_type == ImageType.COLOR:
        res = convert_bgr_to_rgb(res)
    return res 

def dilate(image: np.ndarray, struct_element: np.ndarray, image_type: ImageType) -> np.ndarray:
    if image_type == ImageType.COLOR:
        return dilate_color(image, struct_element)

    m, n = struct_element.shape
    h, w = image.shape
    new_image = np.zeros((h, w), dtype=np.uint8)

    for i in range(h):
        for j in range(w):
            top = max(0, i - m // 2)
            bottom = min(h, i + m // 2 + 1)
            left = max(0, j - n // 2)
            right = min(w, j + n // 2 + 1)
            
            region = image[top:bottom, left:right]
            k = struct_element[
                m // 2 - (i - top) : m // 2 + (bottom - i),
                n // 2 - (j - left) :n // 2 + (right - j)
            ]

            masked = region[k == 1]
            if masked.size == 0:
                continue

            if image_type == ImageType.BLACK_AND_WHITE:
                if np.any(masked == 255):
                    new_image[i, j] = 255
            else:
                new_image[i, j] = np.max(masked)
        
    return new_image

def dilate_color(image: np.ndarray, struct_element: np.ndarray) -> np.ndarray:
    m, n = struct_element.shape
    height, width, channel = image.shape
    new_image = np.zeros((height, width, 3), dtype=np.uint8)

    for ch in range(channel):
        for i in range(height):
            for j in range(width):
                top = max(0, i - m // 2)
                bottom = min(height, i + m // 2 + 1)
                left = max(0, j - n // 2)
                right = min(width, j + n // 2 + 1)

                region = image[top:bottom, left:right, ch]
                k = struct_element[
                    m // 2 - (i - top) : m // 2 + (bottom - i),
                    n // 2 - (j - left) : n // 2 + (right - j)
                ]
                
                masked = region[k == 1]
                if masked.size > 0:
                    new_image[i][j][ch] = np.max(masked)
    
    return new_image

def erode(image: np.ndarray, struct_element: np.ndarray, image_type: ImageType) -> np.ndarray:
    if image_type == ImageType.COLOR:
        return erode_color(image, struct_element)

    m, n = struct_element.shape
    h, w = image.shape
    new_image = np.zeros((h, w), dtype=np.uint8)

    for i in range(h):
        for j in range(w):
            top = max(0, i - m // 2)
            bottom = min(h, i + m // 2 + 1)
            left = max(0, j - n // 2)
            right = min(w, j + n // 2 + 1)

            region = image[top:bottom, left:right]
            k = struct_element[
                m // 2 - (i - top) : m // 2 + (bottom - i),
                n // 2 - (j - left) : n // 2 + (right - j)
            ]
        
            masked = region[k == 1]
            if masked.size == 0:
                continue

            if image_type == ImageType.BLACK_AND_WHITE:
                if np.all(masked == 255):
                    new_image[i, j] = 255
            else:
                new_image[i, j] = np.min(masked)

    return new_image

def erode_color(image: np.ndarray, struct_element: np.ndarray) -> np.ndarray:
    m, n = struct_element.shape
    height, width, channel = image.shape
    new_image = np.zeros((height, width, 3), dtype=np.uint8)

    for ch in range(channel):
        for i in range(height):
            for j in range(width):
                top = max(0, i - m // 2)
                bottom = min(height, i + m // 2 + 1)
                left = max(0, j - n // 2)
                right = min(width, j + n // 2 + 1)

                region = image[top:bottom, left:right, ch]
                k = struct_element[
                    m // 2 - (i - top) : m // 2 + (bottom - i),
                    n // 2 - (j - left) : n // 2 + (right - j)
                ]

                masked = region[k == 1]
                if masked.size > 0:
                    new_image[i][j][ch] = np.min(masked)

    return new_image

def opening(image: np.ndarray, struct_element: np.ndarray, image_type: ImageType) -> np.ndarray:
    return dilate(erode(image, struct_element, image_type), struct_element, image_type)

def closing(image: np.ndarray, struct_element: np.ndarray, image_type: ImageType) -> np.ndarray:
    return erode(dilate(image, struct_element, image_type), struct_element, image_type)

def contour_extraction(image: np.ndarray, struct_element: np.ndarray, image_type: ImageType) -> np.ndarray:
    dilated = dilate(image, struct_element, image_type)
    eroded = erode(image, struct_element, image_type)

    result = dilated.astype(np.int16) - eroded.astype(np.int16)
    return np.clip(result, 0, 255).astype(np.uint8)

def top_hat(image: np.ndarray, struct_element: np.ndarray, image_type: ImageType) -> np.ndarray:
    opened = opening(image, struct_element, image_type)
    result = image.astype(np.int16) - opened.astype(np.int16)
    return np.clip(result, 0, 255).astype(np.uint8)

def bottom_hat(image: np.ndarray, struct_element: np.ndarray, image_type: ImageType) -> np.ndarray:
    closed = closing(image, struct_element, image_type)
    result = closed.astype(np.int16) - image.astype(np.int16)
    return np.clip(result, 0, 255).astype(np.uint8)

def convert_bgr_to_rgb(bgr_image):
    rgb_image = np.zeros_like(bgr_image)
    rgb_image[:, :, 0] = bgr_image[:, :, 2]
    rgb_image[:, :, 1] = bgr_image[:, :, 1]
    rgb_image[:, :, 2] = bgr_image[:, :, 0]

    return rgb_image