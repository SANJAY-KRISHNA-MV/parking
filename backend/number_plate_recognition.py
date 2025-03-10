from ultralytics import YOLO
import cv2
import numpy as np
from heapq import heappush, heappushpop
from collections import Counter
from typing import List, Tuple, Optional
from paddleocr import PaddleOCR
import os

# Load the YOLO model
MODEL_PATH = r'../backend/models/PlateYOLO.pt'
model = YOLO(MODEL_PATH)

class PlateOCR:
    def __init__(self, language: str = 'en', use_angle_cls: bool = True) -> None:
        """
        Initialize the OCR model with specified parameters.

        Args:
            language (str): Language model to use for OCR. Defaults to 'en'.
            use_angle_cls (bool): Whether to use angle classification. Defaults to True.
        """
        self.model = PaddleOCR(use_angle_cls=use_angle_cls, lang=language, show_log=False)

    def extract_text(self, image) -> str:
        """
        Extract text from the provided preprocessed image.

        Args:
            image: Preprocessed input image (numpy array).

        Returns:
            str: Extracted text as a single string.
        """
        try:
            results = self.model.ocr(image)

            if not results or not results[0]:
                return ""

            # Extract text values and combine them
            extracted_values = [item[1][0] for item in results[0]]
            return " ".join(extracted_values)

        except Exception as e:
            print(f"Error during OCR processing: {str(e)}")
            return ""

ocr_model = PlateOCR()

class PlateDetector:
    def __init__(self, conf_threshold: float = 0.85, cooldown_frames: int = 15, top_k: int = 7):
        self.conf_threshold = conf_threshold
        self.cooldown_frames = cooldown_frames
        self.current_cooldown = 0
        self.top_k = top_k
        self.top_detections = []

    def _process_plate_region(self, plate_region: np.ndarray) -> Optional[np.ndarray]:
        if plate_region.size == 0:
            return None

        plate_gray = cv2.cvtColor(plate_region, cv2.COLOR_BGR2GRAY)
        _, plate_thresh = cv2.threshold(plate_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return plate_thresh

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, bool]:
        results = model(frame)
        processed_frame = frame.copy()
        stop_detection = False

        if self.current_cooldown > 0:
            self.current_cooldown -= 1

        for result in results:
            boxes = result.boxes
            for box in boxes:
                if box.cls == 0:
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)

                    color = (0, 255, 0) if conf >= self.conf_threshold else (0, 165, 255)
                    cv2.rectangle(processed_frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(processed_frame, f'Conf: {conf:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                    if conf >= self.conf_threshold and self.current_cooldown == 0:
                        plate_region = frame[y1:y2, x1:x2]
                        processed_plate = self._process_plate_region(plate_region)

                        if processed_plate is not None:
                            if len(self.top_detections) < self.top_k:
                                heappush(self.top_detections, (-conf, processed_plate))
                            else:
                                heappushpop(self.top_detections, (-conf, processed_plate))

                            self.current_cooldown = self.cooldown_frames

                            if len(self.top_detections) >= self.top_k:
                                stop_detection = True

        cv2.putText(processed_frame, f'Threshold: {self.conf_threshold}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (0, 255, 0), 2)
        cv2.putText(processed_frame, f'Top Detections: {len(self.top_detections)}/{self.top_k}', (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        return processed_frame, stop_detection

    def get_top_plates(self) -> List[Tuple[float, np.ndarray]]:
        return [(-(conf), plate) for conf, plate in sorted(self.top_detections)]

    def clear_detections(self):
        self.top_detections = []

def extract_number_plate(video_path: str):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video: {video_path}")
        return None

    detector = PlateDetector(conf_threshold=0.85)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            _, stop_detection = detector.process_frame(frame)
            if stop_detection:
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

    top_plates = detector.get_top_plates()
    if top_plates:
        ocr_results = []
        for conf, plate_img in top_plates:
            try:
                # Pass the plate image to the OCR model
                result = ocr_model.extract_text(plate_img)
                if result:
                    ocr_results.append(result)
            except Exception as e:
                print(f"OCR Error on plate with confidence {conf:.2f}: {str(e)}")

        if ocr_results:
            final_result = Counter(ocr_results).most_common(1)[0][0]
            detector.clear_detections()
            return final_result

    detector.clear_detections()
    return None

if __name__ == "__main__":
    # Example usage (for testing)
    video_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "videos", "your_video.mp4") # path to video.
    number_plate = extract_number_plate(video_path)
    if number_plate:
        print(f"Number plate: {number_plate}")
    else:
        print("Number plate not found.")