from paddleocr import PaddleOCR
import cv2
import os

def extract_number_plate(video_path):
    """
    Extracts number plate from a video using PaddleOCR.

    Args:
        video_path (str): Path to the video file.

    Returns:
        str: Extracted number plate text, or None if not found.
    """
    ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)  # Initialize PaddleOCR
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Error: Could not open video.")
        return None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        result = ocr.ocr(frame, cls=True)
        for res in result:
            for line in res:
                if len(line) > 0:
                    text = line[1][0]
                    # basic filtering to find number plate like strings.
                    if len(text)>5:
                        print(f"Detected: {text}")
                        cap.release()
                        cv2.destroyAllWindows()
                        return text
    cap.release()
    cv2.destroyAllWindows()
    return None

if __name__ == "__main__":
    # Example usage (for testing)
    video_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "videos", "your_video.mp4") # path to video.
    number_plate = extract_number_plate(video_path)
    if number_plate:
        print(f"Number plate: {number_plate}")
    else:
        print("Number plate not found.")