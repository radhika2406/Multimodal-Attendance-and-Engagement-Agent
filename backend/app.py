
import asyncio
import csv
import time
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect

from backend.core.face_detection import FaceDetector
from backend.core.face_tracking import FaceTracker
from backend.core.attendance import AttendanceManager

app = FastAPI(
    title="Multimodal Attendance & Engagement Agent",
    version="1.1.0",
)

detector = FaceDetector()
tracker = FaceTracker(max_missing_frames=20)
attendance = AttendanceManager(
    threshold_seconds=60,
    output_dir="attendance_logs",
)

session_running = False
frame_lock = asyncio.Lock()


@app.get("/")
def home():
    return {
        "message": "Attendance API is running",
        "status": "ready",
        "camera_mode": "browser",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/attendance/start")
async def start_attendance():
    global session_running

    async with frame_lock:
        if session_running:
            return {"message": "Attendance session is already running"}

        tracker.reset()
        attendance.reset()
        session_running = True

    return {
        "message": "Attendance session started. Enable the browser camera.",
        "status": "running",
    }


@app.post("/attendance/frame")
async def process_browser_frame(request: Request):
    """Process one JPEG frame sent by the browser dashboard."""

    if not session_running:
        raise HTTPException(
            status_code=409,
            detail="Start an attendance session before sending frames.",
        )

    raw = await request.body()

    if not raw:
        raise HTTPException(status_code=400, detail="Empty image.")

    image = cv2.imdecode(
        np.frombuffer(raw, dtype=np.uint8),
        cv2.IMREAD_COLOR,
    )

    if image is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid image. Send a JPEG frame.",
        )

    async with frame_lock:
        if not session_running:
            raise HTTPException(
                status_code=409,
                detail="The attendance session has stopped.",
            )

        now = time.monotonic()

        detections = await asyncio.to_thread(
            detector.process_frame, image
        )

        tracks = tracker.update(detections, timestamp=now)

        visible_ids = [
            track["participant_id"] for track in tracks
        ]

        records = attendance.update(
            visible_ids, timestamp=now
        )

        return {
            "status": "running",
            "detected_faces": len(tracks),
            "participants": list(records.values()),
        }


@app.get("/attendance")
def get_attendance():
    return {
        "participants": list(
            attendance.get_attendance().values()
        ),
        "csv_path": attendance.csv_path,
        "status": "running" if session_running else "stopped",
    }


@app.get("/attendance/history")
def get_attendance_history():
    """Return saved session history to the hosted dashboard."""

    path = Path(attendance.csv_path)

    if not path.exists() or path.stat().st_size == 0:
        return {"records": []}

    try:
        with path.open(
            "r", newline="", encoding="utf-8-sig"
        ) as file:
            return {"records": list(csv.DictReader(file))}
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not read attendance history: {exc}",
        ) from exc


@app.post("/attendance/stop")
async def stop_attendance():
    global session_running

    async with frame_lock:
        if not session_running:
            return {"message": "No active attendance session"}

        session_running = False
        records = attendance.finish()

    return {
        "message": "Attendance session stopped and saved.",
        "participants": list(records.values()),
        "csv_path": attendance.csv_path,
    }


@app.websocket("/ws/attendance")
async def attendance_websocket(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            await websocket.send_json({
                "status": (
                    "running" if session_running else "stopped"
                ),
                "participants": list(
                    attendance.get_attendance().values()
                ),
            })
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass
