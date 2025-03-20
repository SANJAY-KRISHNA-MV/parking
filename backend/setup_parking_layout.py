import cv2
import json

def select_rois(image_path):
    """
    Interactively selects ROIs for each slot and saves them to parking_layout.json.
    """
    img = cv2.imread(image_path)
    if img is None:
        print("Image not found or invalid.")
        return

    slots = []
    temp_img = img.copy()  # Create a copy to draw on

    while True:
        roi = cv2.selectROI("Select ROI", temp_img, fromCenter=False, showCrosshair=True)
        if roi == (0, 0, 0, 0):  # Press Enter to finish
            break
        x, y, w, h = roi
        slots.append({"id": f"slot{len(slots) + 1}", "roi": [x, y, x + w, y + h]})

        # Draw the ROI and slot ID on the image
        cv2.rectangle(temp_img, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Green rectangle
        cv2.putText(temp_img, f"Slot {len(slots)}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.imshow("Select ROI", temp_img)  # Update the displayed image

    with open("parking_layout.json", "w") as f:
        json.dump({"slots": slots}, f, indent=4)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    image_path = "../videos/parking_layout_setup.jpg"  # Path to your setup image
    select_rois(image_path)