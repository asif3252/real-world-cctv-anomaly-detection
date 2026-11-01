"""Local single-camera pilot. Credentials stay in memory; no cloud inference."""
import os
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp'
os.environ['OPENCV_LOG_LEVEL'] = 'SILENT'
import csv
import math
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
import tkinter as tk
from tkinter import simpledialog, messagebox


class Events:
    def __init__(self, dwell=30, persistence=2, cooldown=60):
        self.dwell, self.persistence, self.cooldown = dwell, persistence, cooldown
        self.people = {}

    def update(self, now, inside_ids):
        # Strict continuous observations: missed detections reset dwell.
        self.people = {k: v for k, v in self.people.items() if k in inside_ids}
        events = []
        for identity in inside_ids:
            state = self.people.setdefault(identity, {'since': now, 'intrusion': -math.inf, 'loitering': -math.inf})
            elapsed = now - state['since']
            for kind, threshold in [('intrusion', self.persistence), ('loitering', self.dwell)]:
                if elapsed >= threshold and now - state[kind] >= self.cooldown:
                    state[kind] = now
                    events.append((identity, kind, elapsed))
        return events


def main():
    import cv2
    from ultralytics import YOLO
    root = tk.Tk()
    root.withdraw()
    host = simpledialog.askstring('NVR address', 'Enter the local NVR IP from SmartPSS Devices (no http://):')
    if not host:
        return
    host = host.strip()
    if any(c in host for c in '/@?# '):
        messagebox.showerror('Address', 'Enter only the IP address or hostname.')
        return
    port = simpledialog.askinteger('RTSP port', 'RTSP port (not SmartPSS port 37777):', initialvalue=554, minvalue=1, maxvalue=65535)
    channel = simpledialog.askinteger('Camera', 'NVR channel number (choose one of your 25 connected cameras):', initialvalue=1, minvalue=1, maxvalue=32)
    username = simpledialog.askstring('Login', 'NVR username:')
    password = simpledialog.askstring('Login', 'NVR password (kept in memory only):', show='*')
    dwell = simpledialog.askinteger('Loitering', 'Continuous seconds inside the area before loitering alert:', initialvalue=30, minvalue=3, maxvalue=3600)
    if None in (port, channel, username, password, dwell):
        return
    url = f'rtsp://{quote(username, safe="")}:{quote(password, safe="")}@{host}:{port}/cam/realmonitor?channel={channel}&subtype=1'
    messagebox.showinfo('Starting', 'The first launch downloads YOLO11n weights using the internet. Video processing is local. After the video opens, drag a restricted-area rectangle and press Enter. Q stops; R changes the area. Alerts save snapshots and CSV locally. This is an unvalidated pilot.')
    model = YOLO(str(Path(__file__).parent / 'yolo11n.pt'))
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG, [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000, cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000])
    ok, frame = cap.read()
    if not ok:
        cap.release()
        messagebox.showerror('No video', 'Could not read this channel. Verify NVR IP, credentials, RTSP port, channel, and that substream is enabled. No NVR settings were changed.')
        return
    output = Path(__file__).parent / 'events'
    output.mkdir(exist_ok=True)
    rules = Events(dwell)
    roi = None
    last = time.monotonic()
    try:
        while ok:
            height, width = frame.shape[:2]
            ratio = min(1.0, 960 / width)
            frame = cv2.resize(frame, (int(width * ratio), int(height * ratio)))
            if roi is None:
                roi = cv2.selectROI('Choose restricted area', frame, False)
                cv2.destroyWindow('Choose restricted area')
                if roi[2] == 0 or roi[3] == 0:
                    break
            begin = time.monotonic()
            result = model.track(frame, persist=True, classes=[0], conf=0.4, imgsz=640, device='cpu', verbose=False, tracker='bytetrack.yaml')[0]
            inside = set()
            x, y, w, h = roi
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 200, 255), 2)
            boxes = result.boxes
            if boxes is not None and boxes.id is not None:
                for bounds, identity in zip(boxes.xyxy.cpu().tolist(), boxes.id.int().cpu().tolist()):
                    a, b, c, d = map(int, bounds)
                    if x <= (a+c)/2 <= x+w and y <= d <= y+h:
                        inside.add(identity)
                    cv2.rectangle(frame, (a, b), (c, d), (0, 255, 0), 2)
                    cv2.putText(frame, f'Person {identity}', (a, max(20, b)), 0, 0.6, (0, 255, 0), 2)
            now = time.monotonic()
            # A long processing gap cannot establish continuous presence.
            if now - last > 5:
                rules.people.clear()
            last = now
            for identity, kind, elapsed in rules.update(now, inside):
                stamp = datetime.now().astimezone()
                filename = f'{stamp.strftime("%Y%m%d_%H%M%S_%f")}_ch{channel}_{kind}_{identity}.jpg'
                saved = cv2.imwrite(str(output / filename), frame)
                log = output / 'events.csv'
                new = not log.exists()
                with log.open('a', newline='', encoding='utf-8') as handle:
                    writer = csv.writer(handle)
                    if new:
                        writer.writerow(['time', 'channel', 'event', 'track_id', 'dwell_seconds', 'snapshot'])
                    writer.writerow([stamp.isoformat(), channel, kind, identity, round(elapsed, 1), filename if saved else 'WRITE_FAILED'])
                print(f'{stamp.isoformat()} | Channel {channel} | {kind} | Track {identity}')
                root.bell()
            fps = 1 / max(0.001, time.monotonic() - begin)
            cv2.putText(frame, f'PILOT | CH {channel} | inference {fps:.1f} FPS | Q quit / R area', (10, 25), 0, 0.55, (255, 255, 255), 2)
            cv2.imshow('CCTV anomaly pilot', frame)
            key = cv2.waitKey(1) & 255
            if key == ord('q'):
                break
            if key == ord('r'):
                roi = None
                rules.people.clear()
            ok, frame = cap.read()
        if not ok:
            messagebox.showwarning('Stream disconnected', 'The video stream stopped. Detection is no longer running. Restart the application after checking the connection.')
    finally:
        cap.release()
        cv2.destroyAllWindows()
        root.destroy()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        # Do not print exception objects: decoder errors may contain the RTSP URL.
        print('The pilot stopped. Check Python dependencies, model download, network connectivity, and output-folder permissions. Credentials were not saved.')

