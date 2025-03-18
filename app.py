from flask import Flask, request, jsonify, send_from_directory
import uuid
import os
from PIL import Image
from werkzeug.utils import secure_filename
from ultralytics import YOLO
from flask_cors import CORS
from urllib.parse import quote
import cv2
import numpy as np
import threading
from functools import wraps
from datetime import datetime
from pymongo import MongoClient
from datetime import datetime

# การตั้งค่า Flask
app = Flask(__name__)
CORS(app)

# เชื่อมต่อ MongoDB
MONGO_URI = "mongodb://localhost:27017"  # เปลี่ยนตามการตั้งค่าของคุณ
client = MongoClient(MONGO_URI)
db = client["api_database"]
api_keys_collection = db["api_keys"]

# โฟลเดอร์สำหรับอัปโหลด
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# โหลดโมเดลสำหรับการทำนาย (ต้องโหลดโมเดลให้ถูกต้อง)
model_porn = YOLO(os.path.join(os.path.dirname(__file__), 'models', 'best-porn.pt')) # โหลดโมเดลสำหรับตรวจจับเนื้อหาผิดปกติ
model_weapon = YOLO(os.path.join(os.path.dirname(__file__), 'models', 'best-weapon2.pt'))  # โหลดโมเดลสำหรับตรวจจับอาวุธ
model_cigarette = YOLO(os.path.join(os.path.dirname(__file__), 'models', 'best-cigarette.pt'))  # โหลดโมเดลสำหรับตรวจจับบุหรี่

# รายการของ labels ที่ไม่เหมาะสม
INAPPROPRIATE_LABELS = {}
WEAPON_LABELS = {}
CIGARETTE_LABELS = {}

# กำหนดค่า threshold สำหรับการพิจารณาว่าเป็นเนื้อหาที่ไม่เหมาะสมหรือมีอาวุธ
INAPPROPRIATE_CONFIDENCE_THRESHOLD = 0.1
WEAPON_CONFIDENCE_THRESHOLD = 0.1
CIGARETTE_CONFIDENCE_THRESHOLD = 0.1

# ฟังก์ชันสำหรับการวิเคราะห์ภาพ
def analyze_porn(image_path, results_dict):
    results_dict["porn"] = model_porn.predict(source=image_path)

def analyze_weapon(image_path, results_dict):
    results_dict["weapon"] = model_weapon.predict(source=image_path)

def analyze_cigarette(image_path, results_dict):
    results_dict["cigarette"] = model_cigarette.predict(source=image_path)

# ใช้ Dictionary เก็บผลลัพธ์
results_dict = {}

# ฟังก์ชันตรวจสอบประเภทไฟล์ (รองรับทุกประเภท)
def allowed_file(filename):
    return '.' in filename  # ตรวจสอบว่ามี "." ในชื่อไฟล์

# ฟังก์ชันตรวจสอบว่าเป็นไฟล์ภาพจริง
def is_image(file_path):
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except (IOError, SyntaxError):
        return False

# ฟังก์ชันแปลง .jfif เป็น .jpg
def convert_jfif_to_jpg(input_path):
    output_path = input_path.rsplit('.', 1)[0] + '.jpg'
    with Image.open(input_path) as img:
        img.convert('RGB').save(output_path, 'JPEG')
    os.remove(input_path)  # ลบไฟล์เดิม
    return output_path

# ฟังก์ชันวาด Bounding Box
def draw_bounding_boxes(image_path, detections, output_path):
    image = cv2.imread(image_path)
    
    for detection in detections:
        x1, y1, x2, y2 = map(int, detection["bbox"])  # แปลงพิกัดจาก float เป็น int
        label = detection["label"]
        confidence = detection["confidence"]

        # ตรวจสอบขนาดของ Bounding Box เพื่อให้ไม่เกินขนาดของภาพ
        image_height, image_width = image.shape[:2]
        x1 = max(0, min(x1, image_width - 1))
        y1 = max(0, min(y1, image_height - 1))
        x2 = max(0, min(x2, image_width - 1))
        y2 = max(0, min(y2, image_height - 1))

        # วาด Bounding Box
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)  # สีเขียว

        # สร้างข้อความที่ต้องการแสดง
        text = f"{label} ({confidence:.2f})"
        
        # วัดขนาดข้อความ
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
        
        # วาดพื้นหลังข้อความ
        background_rect = (x1, y1 - text_size[1] - 10, x1 + text_size[0], y1)
        cv2.rectangle(image, (background_rect[0], background_rect[1]), 
                      (background_rect[2], background_rect[3]), (0, 255, 0), -1)  # สีเขียวทึบ

        # วาดข้อความ
        cv2.putText(image, text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    cv2.imwrite(output_path, image)

# ฟังก์ชันสำหรับลบไฟล์
def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"Deleted file: {file_path}")
    except Exception as e:
        print(f"Error deleting file: {e}")

# Decorator ตรวจสอบ API Key จาก MongoDB
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('x-api-key')
        if not api_key or not api_keys_collection.find_one({"api_key": api_key}):
            return jsonify({'error': 'Invalid or missing API key'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ฟังก์ชันสำหรับตรวจสอบ Referer
def check_referer(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        referer = request.headers.get('Referer')
        if not referer or "your-website-domain.com" not in referer:
            return jsonify({'error': 'Unauthorized request, referer header is invalid'}), 403
        return f(*args, **kwargs)
    return decorated_function

# API วิเคราะห์ภาพ
@app.route('/analyze-image', methods=['POST'])
@require_api_key  # ตรวจสอบ API Key ก่อนเรียกใช้งาน
def analyze_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400

        file = request.files['image']
        ext = file.filename.rsplit('.', 1)[-1].lower()
        filename = f"{uuid.uuid4()}.{ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        if not is_image(file_path):
            os.remove(file_path)
            return jsonify({'error': 'File is not a valid image'}), 400

        # ใช้ OpenCV โหลดภาพเพียงครั้งเดียว
        image = cv2.imread(file_path)

        # ใช้ Dictionary เก็บผลลัพธ์
        results_dict = {}

        # สร้าง Thread แยกสำหรับแต่ละโมเดล
        thread_porn = threading.Thread(target=analyze_porn, args=(file_path, results_dict))
        thread_weapon = threading.Thread(target=analyze_weapon, args=(file_path, results_dict))
        thread_cigarette = threading.Thread(target=analyze_cigarette, args=(file_path, results_dict))

        # เริ่มรันทั้งสาม Thread
        thread_porn.start()
        thread_weapon.start()
        thread_cigarette.start()

        # รอให้ทั้งสาม Thread ทำงานเสร็จ
        thread_porn.join()
        thread_weapon.join()
        thread_cigarette.join()

        results_porn = results_dict["porn"]
        results_weapon = results_dict["weapon"]
        results_cigarette = results_dict["cigarette"]

        # ประมวลผลผลลัพธ์ของโมเดล porn
        detections_porn = []
        for result in results_porn:
            for box in result.boxes:
                label = model_porn.names[int(box.cls)].lower()
                confidence = float(box.conf)
                bbox = box.xyxy.tolist()[0]  # ใช้พิกัด x1, y1, x2, y2 แทน
                detections_porn.append({
                    "label": label,
                    "confidence": confidence,
                    "bbox": bbox
                })

        # ประมวลผลผลลัพธ์ของโมเดล weapon
        detections_weapon = []
        for result in results_weapon:
            for box in result.boxes:
                label = model_weapon.names[int(box.cls)].lower()
                confidence = float(box.conf)
                bbox = box.xyxy.tolist()[0]  # ใช้พิกัด x1, y1, x2, y2 แทน
                detections_weapon.append({
                    "label": label,
                    "confidence": confidence,
                    "bbox": bbox
                })

        # ประมวลผลผลลัพธ์ของโมเดล cigarette
        detections_cigarette = []
        for result in results_cigarette:
            for box in result.boxes:
                label = model_cigarette.names[int(box.cls)].lower()
                confidence = float(box.conf)
                bbox = box.xyxy.tolist()[0]  # ใช้พิกัด x1, y1, x2, y2 แทน
                detections_cigarette.append({
                    "label": label,
                    "confidence": confidence,
                    "bbox": bbox
                })

        # วาด Bounding Box
        result_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'processed_' + filename)
        draw_bounding_boxes(file_path, detections_porn + detections_weapon + detections_cigarette, result_image_path)

        # กำหนดสถานะ
        status = "passed"
        if any(d["confidence"] >= 0.5 for d in detections_porn) or any(d["confidence"] >= 0.5 for d in detections_weapon) or any(d["confidence"] >= 0.5 for d in detections_cigarette):
            status = "failed"

        # ลบไฟล์ที่อัปโหลด
        os.remove(file_path)
        # ตั้งค่าให้ลบไฟล์ภาพที่ประมวลผลหลังจาก 5 วินาที
        threading.Timer(5, delete_file, args=[result_image_path]).start()

        return jsonify({
            'status': status,
            'detections_porn': detections_porn,
            'detections_weapon': detections_weapon,
            'detections_cigarette': detections_cigarette,
            'processed_image_url': f'http://127.0.0.1:5000/uploads/{quote("processed_" + filename)}'
        })

    except Exception as e:
        return jsonify({'error': f'Error during analysis: {e}'}), 500

# API สำหรับขอ API Key
@app.route('/request-api-key', methods=['POST'])
def request_api_key():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    existing_user = api_keys_collection.find_one({"email": email})
    if existing_user:
        return jsonify({'apiKey': existing_user['api_key']})  # คืนค่า API Key เดิมหากเคยสมัครแล้ว

    api_key = str(uuid.uuid4())
    api_keys_collection.insert_one({"email": email, "api_key": api_key})

    return jsonify({'apiKey': api_key})

# API สำหรับรายงานปัญหา
@app.route('/report-issue', methods=['POST'])
def report_issue():
    issue = request.json.get('issue')
    if issue:
        folder = 'report-issues'
        if not os.path.exists(folder):
            os.makedirs(folder)

        # Use current time as filename (formatted)
        filename = f"report-issues/report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        
        with open(filename, 'w') as file:
            file.write(issue + '\n')
        return jsonify({'success': True}), 200
    return jsonify({'success': False}), 400

# API สำหรับดาวน์โหลดเอกสารคู่มือ
@app.route('/download-manual', methods=['GET'])
def download_manual():
    manual_path = os.path.join(os.getcwd(), 'manual.pdf')  # ใช้เส้นทางที่ถูกต้อง
    if os.path.exists(manual_path):
        return send_from_directory(os.getcwd(), 'manual.pdf', as_attachment=True)
    return jsonify({'error': 'ไม่พบไฟล์เอกสารคู่มือ'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
