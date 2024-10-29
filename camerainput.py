import tkinter as tk
from tkinter import messagebox
import cv2
import os
import datetime
import easygui as eg
import psycopg2

# Database connection details (replace with actual values)
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "Sp00ky!"
DB_HOST = "localhost"
DB_PORT = "12345"

# Connect to the database
def connect_db():
    try:
        return psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

# Check if there is an active session for any user
def check_login_status():
    conn = connect_db()
    if not conn:
        return False  # If the database connection fails, deny access

    try:
        with conn.cursor() as cur:
            # Check if there is any active session
            cur.execute('SELECT 1 FROM "FaceUsers".sessions LIMIT 1')
            result = cur.fetchone()
            return result is not None
    finally:
        conn.close()

# Access the camera if the user is logged in
def access_camera():
    if not check_login_status():
        eg.msgbox("Access denied. Please log in first.", "Error")
        return

    save_directory = 'camerainput screenshots'
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    cv2.namedWindow("preview")
    vc = cv2.VideoCapture(0)  # Use '0' for the default camera

    if vc.isOpened():
        rval, frame = vc.read()
    else:
        rval = False

    while rval:
        cv2.imshow("preview", frame)
        rval, frame = vc.read()
        key = cv2.waitKey(20)
        if key == 27:  # exit on ESC
            break
        elif key == ord('s'):  # Save screenshot on pressing 's'
            timestamp = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
            screenshot_filename = f"screenshot_{timestamp}.png"
            screenshot_path = os.path.join(save_directory, screenshot_filename)
            cv2.imwrite(screenshot_path, frame)
            print(f"Screenshot saved as {screenshot_filename}")

    vc.release()
    cv2.destroyWindow("preview")

if __name__ == "__main__":
    access_camera()
