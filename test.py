import cv2

# Public camera URL (HTTP or RTSP)
stream_url = "https://www.earthcam.com/myearthcam/guapiarain"
stream_url="https://www.skylinewebcams.com/4e15c1e9-199c-4868-9b21-4e758a472666"

def get_frame():
    cap = cv2.VideoCapture(stream_url)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None
    
    # Encode frame as JPEG
    ret, jpeg = cv2.imencode('.jpg', frame)
    if not ret:
        return None

    return jpeg.tobytes()

get_frame()