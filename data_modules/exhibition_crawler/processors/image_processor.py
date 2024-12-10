import cv2
import numpy as np
import os
import requests
import logging
import math

def sanitize_filename(filename):
    filename = filename.replace('［', '').replace('］', '')
    filename = filename.replace('[', '').replace(']', '')
    filename = filename.replace('＆', 'and')
    filename = filename.replace('&', 'and')
    filename = filename.replace(':', '_')
    filename = filename.replace('/', '_')
    filename = filename.replace('|', '_')
    filename = ' '.join(filename.split())
    filename = filename.strip()
    return filename

class ImageProcessor:
    def __init__(self):
        self.temp_images = {}
        self.processed_images = {}

    @staticmethod
    def _sanitize_filename(filename):
        return sanitize_filename(filename)

    def save_image(self, img_url, name, img_number):
        try:
            response = requests.get(img_url, stream=True)
            if response.status_code == 200:
                if name not in self.temp_images:
                    self.temp_images[name] = []
                self.temp_images[name].append(response.content)
                logging.info(f"이미지 {img_number} 임시 저장 완료: {name}")
            else:
                logging.error(f"이미지 다운로드 실패 (상태 코드: {response.status_code}): {img_url}")
        except Exception as img_error:
            logging.error(f"이미지 다운로드 중 오류: {str(img_error)}")

    def combine_and_save_images(self, name):
        try:
            if name not in self.temp_images or not self.temp_images[name]:
                logging.warning(f"{name}의 저장된 이미지가 없습니다")
                return
            
            images = []
            max_width = 0
            total_height = 0
            
            for idx, img_data in enumerate(self.temp_images[name]):
                try:
                    nparr = np.frombuffer(img_data, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if img is None:
                        continue
                    
                    if img.shape[1] > 1500:
                        scale = 1500 / img.shape[1]
                        new_width = 1500
                        new_height = int(img.shape[0] * scale)
                        img = cv2.resize(img, (new_width, new_height))
                    
                    processed_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    images.append(processed_img)
                    max_width = max(max_width, processed_img.shape[1])
                    total_height += processed_img.shape[0]
                except Exception as e:
                    print(f"이미지 {idx+1} 처리 중 오류: {str(e)}")
            
            if not images:
                return
            
            combined = np.zeros((total_height, max_width, 3), dtype=np.uint8)
            y_offset = 0
            for img in images:
                if len(img.shape) == 2:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                h, w = img.shape[:2]
                x_offset = (max_width - w) // 2
                combined[y_offset:y_offset+h, x_offset:x_offset+w] = img
                y_offset += h
            
            segments = self._split_image_with_overlap(combined)
            self.processed_images[name] = segments
            
            del self.temp_images[name]
            
        except Exception as e:
            logging.error(f"전체 처리 중 에러: {str(e)}")

    def _split_image_with_overlap(self, image, overlap_percent=20):
        height, width = image.shape[:2]
        aspect_ratio = height / width
        base_segment_height = width * 3
        
        if aspect_ratio > 5:
            num_vertical = math.ceil(height / base_segment_height)
        else:
            num_vertical = 1
        
        segment_height = height // num_vertical
        overlap_pixels = int(segment_height * overlap_percent / 100)
        segments = []
        
        for i in range(num_vertical):
            start_y = max(0, i * segment_height - overlap_pixels)
            end_y = min(height, (i + 1) * segment_height + overlap_pixels)
            segment = image[start_y:end_y, 0:width]
            segments.append(segment)
        
        return segments 