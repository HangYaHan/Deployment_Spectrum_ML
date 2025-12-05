import cv2
import argparse
import time
import os
import platform

#!/usr/bin/env python3
# test_camera.py
# Simple camera test program. Press q to quit, s to save the current frame.
# Requires: opencv-python


def list_cameras(max_index=8):
    found = []
    api = cv2.CAP_DSHOW if platform.system() == "Windows" else 0
    for i in range(max_index):
        cap = cv2.VideoCapture(i, api)
        if not cap.isOpened():
            cap.release()
            continue
        ret, _ = cap.read()
        if ret:
            found.append(i)
        cap.release()
    return found


def main():
    parser = argparse.ArgumentParser(description="Camera test (press q to quit, s to save)")
    parser.add_argument("--device", type=int, default=0, help="camera device index")
    parser.add_argument("--width", type=int, default=640, help="frame width")
    parser.add_argument("--height", type=int, default=480, help="frame height")
    parser.add_argument("--list", action="store_true", help="list available cameras and exit")
    parser.add_argument("--save-dir", type=str, default="captures", help="directory to save screenshots")
    args = parser.parse_args()

    if args.list:
        cams = list_cameras()
        if cams:
            print("Found camera indices:", cams)
        else:
            print("No available cameras found")
        return

    os.makedirs(args.save_dir, exist_ok=True)

    api = cv2.CAP_DSHOW if platform.system() == "Windows" else 0
    cap = cv2.VideoCapture(args.device, api)
    if not cap.isOpened():
        print(f"Unable to open camera {args.device}")
        return

    # Attempt to set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    prev_time = time.time()
    frame_count = 0
    fps = 0.0

    window_name = f"Camera {args.device} - q:quit  s:save"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame")
            break

        frame_count += 1
        now = time.time()
        if now - prev_time >= 1.0:
            fps = frame_count / (now - prev_time)
            prev_time = now
            frame_count = 0

        # Display info on the image
        txt = f"Device: {args.device}  {frame.shape[1]}x{frame.shape[0]}  FPS: {fps:.1f}"
        cv2.putText(frame, txt, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow(window_name, frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:  # q or ESC
            break
        if key == ord("s"):  # save current frame
            ts = time.strftime("%Y%m%d_%H%M%S")
            fname = os.path.join(args.save_dir, f"capture_{ts}.png")
            cv2.imwrite(fname, frame)
            print("Saved:", fname)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
