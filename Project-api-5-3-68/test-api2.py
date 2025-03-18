import requests

# URL ของ API
base_url = 'http://127.0.0.1:5000'

# กำหนด API Key ที่คุณได้รับ
api_key = '459ab12a-2153-4822-8604-2874437990d6'  # เปลี่ยนเป็น API Key ของคุณ

# ฟังก์ชันทดสอบการวิเคราะห์ภาพด้วย API Key
def test_analyze_image_with_api_key():
    # เปลี่ยน path เป็นไฟล์ภาพที่คุณต้องการทดสอบ
    image_path = r"C:\Users\lovew\OneDrive\Music\หญิง+bikini.jpeg"
    with open(image_path, 'rb') as image_file:
        headers = {'x-api-key': api_key}
        response = requests.post(f'{base_url}/analyze-image', headers=headers, files={'image': image_file})
        print(response.json())

# เริ่มการทดสอบ
if __name__ == '__main__':
    # ทดสอบการวิเคราะห์ภาพ
    test_analyze_image_with_api_key()
