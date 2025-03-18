// Initializing particles.js background effect
particlesJS("particles-js", {
  particles: {
    number: {
      value: 80,
      density: {
        enable: true,
        value_area: 800
      }
    },
    color: {
      value: "#ffffff"
    },
    shape: {
      type: "circle",
      stroke: {
        width: 0,
        color: "#000000"
      }
    },
    opacity: {
      value: 0.5,
      random: true,
      anim: {
        enable: true,
        speed: 1,
        opacity_min: 0.1,
        sync: false
      }
    },
    size: {
      value: 5,
      random: true,
      anim: {
        enable: true,
        speed: 40,
        size_min: 0.1,
        sync: false
      }
    },
    line_linked: {
      enable: true,
      distance: 150,
      color: "#ffffff",
      opacity: 0.4,
      width: 1
    },
    move: {
      enable: true,
      speed: 6,
      direction: "none",
      random: false,
      straight: false,
      out_mode: "out",
      bounce: false,
      attract: {
        enable: false,
        rotateX: 600,
        rotateY: 1200
      }
    }
  },
  interactivity: {
    detect_on: "window",
    events: {
      onhover: {
        enable: true,
        mode: "repulse"
      },
      onclick: {
        enable: true,
        mode: "push"
      },
      resize: true
    }
  },
  retina_detect: true
});

// ฟังก์ชันสำหรับอัปโหลดภาพเมื่อคลิกปุ่ม "อัปโหลดรูปภาพ"
function uploadImage() {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*';

  input.onchange = async () => {
    const file = input.files[0];
    if (!file) return;

    // เพิ่มการจัดการอัปโหลดภาพหลังจากเลือกไฟล์
    const formData = new FormData();
    formData.append('image', file);

    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultText = document.getElementById('resultText');
    const imagePreview = document.getElementById('imagePreview');
    const processedImage = document.getElementById('processedImage');

    loadingSpinner.style.display = 'block';
    resultText.textContent = '';
    processedImage.style.display = 'none';

    const reader = new FileReader();
    reader.onload = () => {
      imagePreview.src = reader.result;
      imagePreview.style.display = 'block';
    };
    reader.readAsDataURL(file);

    try {
      const response = await fetch('http://127.0.0.1:5000/analyze-image', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      loadingSpinner.style.display = 'none';

      if (response.ok) {
        const detectionsPorn = data.detections_porn;
        const detectionsWeapon = data.detections_weapon;
        
        if (detectionsPorn.length > 0 || detectionsWeapon.length > 0) {
          resultText.textContent = 'ผลลัพธ์: ไม่ผ่านการทดสอบ';
          resultText.style.color = 'red'; // เปลี่ยนสีเป็นแดง
        } else {
          resultText.textContent = 'ผลลัพธ์: ผ่านการทดสอบ';
          resultText.style.color = 'green'; // เปลี่ยนสีเป็นเขียว
        }

        if (data.processed_image_url) {
          processedImage.src = data.processed_image_url;
          processedImage.style.display = 'block';
        }
      } else {
        resultText.textContent = `ข้อผิดพลาด: ${data.error || 'เกิดข้อผิดพลาด'}`;
        resultText.style.color = 'red'; // เปลี่ยนสีเป็นแดงเมื่อเกิดข้อผิดพลาด
      }
    } catch (error) {
      loadingSpinner.style.display = 'none';
      resultText.textContent = 'ข้อผิดพลาด: ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์';
      resultText.style.color = 'red'; // เปลี่ยนสีเป็นแดงเมื่อเกิดข้อผิดพลาด
    }
  };

  input.click();
}

// ฟังก์ชันขอ API Key
function requestApiKey() {
  const email = prompt('กรุณาใส่อีเมลของคุณเพื่อขอ API Key:');
  if (!email) return;

  fetch('http://127.0.0.1:5000/request-api-key', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  })
    .then((response) => response.json())
    .then((data) => {
      alert(data.apiKey ? `API Key ของคุณคือ: ${data.apiKey}` : `ข้อผิดพลาด: ${data.error}`);
    })
    .catch(() => {
      alert('ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์');
    });
}

// ฟังก์ชันรายงานปัญหา
function reportIssue() {
  const issueDescription = prompt('กรุณาระบุรายละเอียดปัญหาที่คุณพบ:');
  if (!issueDescription) return;

  fetch('http://127.0.0.1:5000/report-issue', {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ issue: issueDescription }),
  })
    .then((response) => response.json())
    .then((data) => {
      alert(data.success ? 'ขอบคุณสำหรับการรายงานปัญหาของคุณ!' : 'ไม่สามารถส่งข้อมูลได้ กรุณาลองใหม่อีกครั้ง');
    })
    .catch(() => {
      alert('ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์');
    });
}

// ฟังก์ชันสำหรับดาวน์โหลดเอกสารคู่มือ
function downloadManual() {
  const url = "http://127.0.0.1:5000/download-manual"; // URL ที่เชื่อมต่อกับ Flask route
  window.location.href = url; // เปลี่ยนหน้าจอไปยัง URL ของ Flask
}


