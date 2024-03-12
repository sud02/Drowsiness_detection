from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
from scipy.spatial import distance
from imutils import face_utils
import imutils
import dlib
import cv2
from pygame import mixer

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

mixer.init()
mixer.music.load("static/music.wav")

def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

thresh = 0.25
frame_check = 20
detect = dlib.get_frontal_face_detector()
predict = dlib.shape_predictor("static/models/shape_predictor_68_face_landmarks.dat")

(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["right_eye"]

class DrowsinessDetection:
    def __init__(self):
        self.cap = None
        self.flag = 0
        self.running_event = asyncio.Event()

    async def start_detection(self, websocket: WebSocket):
        if not self.running_event.is_set():
            self.running_event.set()
            self.cap = cv2.VideoCapture(0)
            await self.detect_drowsiness(websocket)

    async def stop_detection(self):
        if self.running_event.is_set():
            self.running_event.clear()
            if self.cap:
                self.cap.release()
                self.cap = None
            cv2.destroyAllWindows()

    async def detect_drowsiness(self, websocket: WebSocket):
        drowsiness_detected = False
        while self.running_event.is_set():
            ret, frame = self.cap.read()
            if not ret:
                break
            frame = imutils.resize(frame, width=450)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            subjects = detect(gray, 0)
            for subject in subjects:
                shape = predict(gray, subject)
                shape = face_utils.shape_to_np(shape)
                leftEye = shape[lStart:lEnd]
                rightEye = shape[rStart:rEnd]
                leftEAR = eye_aspect_ratio(leftEye)
                rightEAR = eye_aspect_ratio(rightEye)
                ear = (leftEAR + rightEAR) / 2.0
                if ear < thresh:
                    self.flag += 1
                    if self.flag >= frame_check and not drowsiness_detected:
                        mixer.music.play()
                        await websocket.send_text('{"alert": "Drowsiness Detected!"}')
                        drowsiness_detected = True
                else:
                    if drowsiness_detected:
                        print("sending clear msg")
                        await websocket.send_text('{"alert": "clear"}')
                        drowsiness_detected = False
                    self.flag = 0
            await asyncio.sleep(0.01)

detection = DrowsinessDetection()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            if data == "start":
                await detection.start_detection(websocket)
            elif data == "stop":
                await detection.stop_detection()
    except WebSocketDisconnect:
        await detection.stop_detection()

@app.get("/")
async def get():
    return FileResponse('static/index.html')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)