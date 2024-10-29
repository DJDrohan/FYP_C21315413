import cv2
import os
import datetime
import easygui as eg

LOGIN_STATE_FILE = 'login_state.txt'

# Check if the user is logged in by reading the login state file
def check_login_status():
    return os.path.exists(LOGIN_STATE_FILE)

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
