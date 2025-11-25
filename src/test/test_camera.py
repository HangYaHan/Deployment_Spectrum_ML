import cv2
import argparse
import time
import os
import platform

#!/usr/bin/env python3
# test_camera.py
# 简单相机测试程序，按 q 退出，按 s 保存当前帧
# 依赖: opencv-python



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
    parser = argparse.ArgumentParser(description="相机测试 (按 q 退出, s 保存图片)")
    parser.add_argument("--device", type=int, default=0, help="相机设备索引")
    parser.add_argument("--width", type=int, default=640, help="帧宽")
    parser.add_argument("--height", type=int, default=480, help="帧高")
    parser.add_argument("--list", action="store_true", help="列出可用相机并退出")
    parser.add_argument("--save-dir", type=str, default="captures", help="保存截图目录")
    args = parser.parse_args()

    if args.list:
        cams = list_cameras()
        if cams:
            print("发现相机索引:", cams)
        else:
            print("未发现可用相机")
        return

    os.makedirs(args.save_dir, exist_ok=True)

    api = cv2.CAP_DSHOW if platform.system() == "Windows" else 0
    cap = cv2.VideoCapture(args.device, api)
    if not cap.isOpened():
        print(f"无法打开相机 {args.device}")
        return

    # 尝试设置分辨率
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    prev_time = time.time()
    frame_count = 0
    fps = 0.0

    window_name = f"Camera {args.device} - q:退出  s:保存"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("读取帧失败")
            break

        frame_count += 1
        now = time.time()
        if now - prev_time >= 1.0:
            fps = frame_count / (now - prev_time)
            prev_time = now
            frame_count = 0

        # 在图像上显示信息
        txt = f"Device: {args.device}  {frame.shape[1]}x{frame.shape[0]}  FPS: {fps:.1f}"
        cv2.putText(frame, txt, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow(window_name, frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:  # q or ESC
            break
        if key == ord("s"):  # 保存当前帧
            ts = time.strftime("%Y%m%d_%H%M%S")
            fname = os.path.join(args.save_dir, f"capture_{ts}.png")
            cv2.imwrite(fname, frame)
            print("已保存:", fname)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()