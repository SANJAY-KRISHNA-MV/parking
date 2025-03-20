import cv2
import json
from ultralytics import YOLO
import numpy as np

# Load the YOLOv8 model
model_path = r'./models/yolov8m.pt' # working the best yolov8m
model = YOLO(model_path)

# Load parking layout configuration
with open("parking_layout.json", "r") as f:
    parking_layout = json.load(f)

def process_image(image_path):
    """
    Processes the image to detect vehicles and determine slot occupancy.
    """
    try:
        # 1. Load the image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Image not found or invalid")

        # 2. Run YOLOv8 detection
        results = model(img)

        # 3. Determine slot occupancy
        slot_occupancy_status = {}
        for slot in parking_layout["slots"]:
            slot_id = slot["id"]
            slot_roi = slot["roi"]
            slot_occupancy_status[slot_id] = is_slot_occupied(img, slot_roi, results)
        
        # 4. Visualize the results
        visualize_results(img, slot_occupancy_status)
        
        # 5. Return the occupancy status of each slot
        return slot_occupancy_status

    except Exception as e:
        import traceback
        print(f"Error processing image: {e}")
        traceback.print_exc()  # Print full traceback for debugging
        return None

def is_slot_occupied(img, slot_roi, results, iou_threshold=0.5):
    x1, y1, x2, y2 = slot_roi
    slot_area = (x2 - x1) * (y2 - y1)
    
    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy().astype(int)
        scores = result.boxes.conf.cpu().numpy()
        
        for i, box in enumerate(boxes):
            if scores[i] < 0.5:
                continue
                
            bx1, by1, bx2, by2 = box
            
            # Calculate intersection
            inter_x1 = max(x1, bx1)
            inter_y1 = max(y1, by1)
            inter_x2 = min(x2, bx2)
            inter_y2 = min(y2, by2)
            
            if inter_x1 < inter_x2 and inter_y1 < inter_y2:
                inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
                box_area = (bx2 - bx1) * (by2 - by1)
                union_area = slot_area + box_area - inter_area
                iou = inter_area / union_area
                
                if iou > iou_threshold:
                    return True
    
    return False

def visualize_results(img, slot_occupancy_status):
    """
    Visualizes the parking slots and their occupancy status on the image.
    Red = Occupied, Green = Free
    """
    img_copy = img.copy()
    
    # Draw detection boxes from YOLO first (so they're below the parking slots)
    for result in model(img):
        boxes = result.boxes.xyxy.cpu().numpy().astype(int)
        scores = result.boxes.conf.cpu().numpy()
        
        for i, box in enumerate(boxes):
            if scores[i] < 0.5:  # Match the threshold from is_slot_occupied
                continue
                
            bx1, by1, bx2, by2 = box
            cv2.rectangle(img_copy, (bx1, by1), (bx2, by2), (255, 0, 0), 2)  # Blue for detected vehicles
            cv2.putText(img_copy, f"{scores[i]:.2f}", (bx1, by1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
    
    # Draw parking slots
    occupied_count = 0
    free_count = 0
    
    for slot in parking_layout["slots"]:
        slot_id = slot["id"]
        x1, y1, x2, y2 = slot["roi"]
        
        # FIX: Red for occupied, Green for free (corrected)
        is_occupied = slot_occupancy_status[slot_id]
        if is_occupied:
            color = (0, 0, 255)  # Red for occupied
            occupied_count += 1
        else:
            color = (0, 255, 0)  # Green for free
            free_count += 1
            
        cv2.rectangle(img_copy, (x1, y1), (x2, y2), color, 2)
        cv2.putText(img_copy, f"ID: {slot_id}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    # Add summary text
    cv2.putText(img_copy, f"Occupied: {occupied_count}, Free: {free_count}", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Display the image
    cv2.imshow("Parking Slots", img_copy)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    # Save the visualization
    cv2.imwrite("parking_visualization.jpg", img_copy)

if __name__ == "__main__":
    image_path = "../videos/parking_layout_setup.jpg"  # Adjust the path if needed
    slot_status = process_image(image_path)

    if slot_status:
        print("Slot Occupancy Status:")
        for slot, occupied in slot_status.items():
            print(f"Slot {slot}: {'Occupied' if occupied else 'Free'}")
    else:
        print("Image processing failed.")