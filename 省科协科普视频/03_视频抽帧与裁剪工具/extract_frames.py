import cv2
import os
import sys

def extract_frames(video_path, output_dir, end_sec=45.0, interval_sec=0.5):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error opening video file: {video_path}")
        return
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    print(f"Video loaded: {video_path}")
    print(f"FPS: {fps}, Total frames: {total_frames}, Duration: {duration:.2f}s")
    
    frame_interval = int(fps * interval_sec)
    frame_idx = 0
    saved_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        current_sec = frame_idx / fps
        if current_sec > end_sec:
            break
            
        if frame_idx % frame_interval == 0:
            filename = f"frame_{current_sec:05.2f}.jpg"
            filepath = os.path.join(output_dir, filename)
            cv2.imwrite(filepath, frame)
            saved_count += 1
            
        frame_idx += 1
        
    cap.release()
    print(f"Extraction complete. Saved {saved_count} frames to {output_dir}")

if __name__ == "__main__":
    from pathlib import Path
    SCRIPT_DIR = Path(__file__).resolve().parent
    video = SCRIPT_DIR.parent / "02_参考拉片库" / "2026-05-31_10-47_差评君冲浪普拉斯视频切片分析包" / "差评君_前5分钟低清参考片段.mp4"
    if not video.exists():
        video = SCRIPT_DIR.parent / "02_参考拉片库" / "2026-05-31_10-47_差评君冲浪普拉斯视频切片分析包" / "冲浪普拉斯_前5分钟低清参考片段.mp4"
    out_dir = SCRIPT_DIR.parent / "temp_frames"
    extract_frames(str(video), str(out_dir), 45.0, 0.5)
