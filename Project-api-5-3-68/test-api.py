import requests

# URL ของ API
BASE_URL = 'http://127.0.0.1:5000'

# ทดสอบการขอ API Key
def test_request_api_key(email):
    response = requests.post(f'{BASE_URL}/request-api-key', json={'email': email})
    if response.status_code == 200:
        print('API Key:', response.json().get('apiKey'))
    else:
        print('Error requesting API Key:', response.json())

# ทดสอบการวิเคราะห์ภาพ
def test_analyze_image(image_path):
    with open(image_path, 'rb') as img:
        response = requests.post(f'{BASE_URL}/analyze-image', files={'image': img})
        if response.status_code == 200:
            print('Analysis Result:', response.json())
        else:
            print('Error analyzing image:', response.json())

# ทดสอบ protected endpoint
def test_protected_endpoint(api_key):
    headers = {'x-api-key': api_key}
    response = requests.post(f'{BASE_URL}/protected-endpoint', headers=headers)
    if response.status_code == 200:
        print('Protected Endpoint Response:', response.json())
    else:
        print('Error accessing protected endpoint:', response.json())

# เรียกใช้ฟังก์ชันทดสอบ
if __name__ == '__main__':
    # ทดสอบการขอ API Key
    test_request_api_key('your_email@example.com')

    # ทดสอบการวิเคราะห์ภาพ
    test_analyze_image(r'C:\Users\lovew\OneDrive\เอกสาร\คลังภาพ dataset ภาพโป๊เปลือย\รูปโป๊หญิง\หญิง+Bikini.jpg')

    # ทดสอบ protected endpoint
    # แทนที่ 'your_api_key' ด้วย API Key ที่ได้รับ
    test_protected_endpoint('8d899815-bd2b-4865-9494-f76ad3ed0c89')
