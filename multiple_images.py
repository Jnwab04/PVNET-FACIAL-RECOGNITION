import cv2
from deepface import DeepFace
import time
import os
import pandas as pd
import tkinter as tk
from tkinter import messagebox

# Function to get the absolute path of the database folder
def get_db_path():
    # Assuming the database folder is in the same directory as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "Database")
    return db_path

def get_folder_names(database_path):
    matched_image = {}
    folder_name = [name for name in os.listdir(database_path) if os.path.isdir(os.path.join(database_path, name))]
    for i in folder_name:
        matched_image[i] = 0
    return matched_image

# Function to recognize faces in the snapshot image
def recognize_face(snapshot, dict):

    temp_image_path = "temp_snapshot.jpg"
    cv2.imwrite(temp_image_path, snapshot)

    try:
        results = DeepFace.find(img_path=temp_image_path, db_path=db_path, enforce_detection=False, model_name="Facenet512", detector_backend="opencv")
        # print(results[0].head(10))
        if isinstance(results, list) and len(results[0]['identity']) > 0:
            print("Match found:")
            for result_df in results:
                if isinstance(result_df, pd.DataFrame) and 'identity' in result_df.columns:
                    for i in range(len(result_df['identity'])):
                        base_name = os.path.basename(result_df['identity'][i])
                        distance = result_df['distance'][i]
                        distance_inverse_squared = (1-distance)**2
                        print(base_name, distance, distance_inverse_squared)
                        for key in dict:
                            if key in base_name:
                                dict[key] += distance_inverse_squared
            print("Tally dictionary",dict)
            # print("Tally dictionary",dict)
            return dict
        else:
            print("No match found")
            return dict
    except Exception as e:
        print("Error during facial recognition:", str(e))
        return dict
    finally:
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)

def restart_recognition():
    global last_snapshot_time, snapshot_image, num_screenshot, max_key, folders_dict, all_zero, face_detected
    last_snapshot_time = time.time()
    snapshot_image = None
    num_screenshot = 0
    max_key = None
    all_zero = False
    folders_dict = get_folder_names(db_path)
    face_detected = False
    print("Face recognition restarted.")

def run_face_recognition():
    global last_snapshot_time, snapshot_image, num_screenshot, max_key, folders_dict, cap, running, all_zero, face_detected
    # Initialize variables
    last_snapshot_time = time.time()
    snapshot_interval = 5  # seconds
    snapshot_image = None

    num_screenshot = 0
    max_key = None
    all_zero = False
    face_detected = False

    # Create a VideoCapture object to access the webcam
    cap = cv2.VideoCapture(0)
    running = True

    try:
        while running:
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture image")
                break

            # Convert the frame to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect faces in the frame
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE)

            # Draw rectangles around detected faces
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)  # Blue box for all faces
                face_detected = True
                

            if face_detected:
                # Take a snapshot every `snapshot_interval` seconds
                current_time = time.time()
                if current_time - last_snapshot_time >= snapshot_interval:
                    if num_screenshot < 3:
                        # Add a delay of unit 5 from when webcam recognize face to when webcam take a screenshot
                        time.sleep(5)

                        snapshot_image = frame.copy()
                        matched_dict = recognize_face(snapshot_image, folders_dict)
                        # print(matched_dict)
                        num_screenshot += 1
                        last_snapshot_time = current_time
                    if num_screenshot >= 3:
                        all_zero = all(value == 0 for value in matched_dict.values())
                        max_key = max(matched_dict, key=matched_dict.get)
                        face_detected = False
                        # print(max_key)
            if all_zero:
                cv2.putText(frame, f"First time seeing this face!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            elif max_key:
                cv2.putText(frame, f'Good to see you again {max_key}!!', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                # print(f"You are {max_key}")
            
            # Display the live webcam feed with detection boxes
            cv2.imshow('Webcam Feed', frame)

            # Display the snapshot image next to the live feed
            if snapshot_image is not None:
                combined_frame = cv2.hconcat([frame, snapshot_image])
                cv2.imshow('Combined Feed', combined_frame)
            else:
                cv2.imshow('Combined Feed', frame)

            # Press 'q' to exit the loop
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        # Release the webcam and close all OpenCV windows
        cap.release()
        cv2.destroyAllWindows()

def on_quit():
    global running
    running = False
    if cap.isOpened():
        cap.release()
    cv2.destroyAllWindows()
    root.quit()

# Initialize GUI
root = tk.Tk()
root.title("Face Recognition")
frame = tk.Frame(root)
frame.pack()

restart_button = tk.Button(frame, text="Restart Face Recognition", command=restart_recognition)
restart_button.pack(side=tk.LEFT)

quit_button = tk.Button(frame, text="Quit", command=on_quit)
quit_button.pack(side=tk.LEFT)

# Load the pre-trained face detector from OpenCV
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Get the database path
db_path = get_db_path()
folders_dict = get_folder_names(db_path)

# Check if the database path exists
if not os.path.exists(db_path):
    raise FileNotFoundError(f"Database folder not found at {db_path}")


# Start face recognition in a separate thread
import threading
face_recognition_thread = threading.Thread(target=run_face_recognition)
face_recognition_thread.start()

# Run the GUI main loop
root.mainloop()


