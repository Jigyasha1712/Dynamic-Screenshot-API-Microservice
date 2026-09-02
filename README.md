# 📸 Dynamic-Screenshot-API-Microservice

[![Live Demo](https://img.shields.io/badge/Live_Demo-GitHub_Pages-purple?style=for-the-badge&logo=github)](https://jigyasha1712.github.io/Dynamic-Screenshot-API-Microservice/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-black?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Selenium](https://img.shields.io/badge/Selenium-4.x-green?style=for-the-badge&logo=selenium&logoColor=white)](https://selenium.dev)
[![AWS S3](https://img.shields.io/badge/AWS-S3_Storage-orange?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/s3/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

A production-grade **Flask REST API Microservice** designed for high-throughput headless web rendering, automated cookie/modal dismissal, responsive multi-device viewport emulation (Desktop, Mobile, Tablet), and direct **Amazon AWS S3** cloud image storage.

---

## 🌟 Interactive Live Web Demo
Test the live screenshot emulator and REST API curl generator:  
👉 **[https://jigyasha1712.github.io/Dynamic-Screenshot-API-Microservice/](https://jigyasha1712.github.io/Dynamic-Screenshot-API-Microservice/)**

---

## 🚀 Core Features

- **🌐 Headless Dynamic Rendering**: Executes complex single-page apps (SPAs) powered by React, Vue, and Angular with custom JavaScript wait delays.
- **🛡️ Automated Modal & Cookie Dismissal**: Auto-locates and clicks away cookie consents, GDPR banners, and subscription popups.
- **📱 Responsive Viewport Emulation**: Seamlessly switch between Desktop (`1920×1080`), Tablet (`820×1180`), and Mobile (`393×852`).
- **📜 Infinite Full-Page Stitching**: Stitches full-length web pages into a continuous single high-res PNG.
- **☁️ Direct AWS S3 Persistence**: Automatically pipes captured buffers into secure AWS S3 buckets with pre-signed URLs.

---

## 📁 Repository Structure

```
├── index.html                     # Live Interactive Viewport Studio (GitHub Pages)
├── screenshot_api_endpoint.py     # Main Flask microservice REST API controller
├── config.py                      # Headless Chrome options, S3 & environment settings
├── example_usage.py               # Client integration examples (requests, asyncio)
├── test_installation.py           # Health checks & driver validation tests
├── requirements.txt               # Dependencies (Flask, Selenium, Boto3)
├── .env.example                   # Environment configuration template
└── README.md                      # Documentation & API reference
```

---

## 💻 Local API Quickstart

```bash
# Clone the repository
git clone https://github.com/Jigyasha1712/Dynamic-Screenshot-API-Microservice.git

# Install dependencies
pip install -r requirements.txt

# Run the Flask Microservice
python screenshot_api_endpoint.py
```

### API Endpoint Usage:
```bash
curl -X POST http://localhost:5000/api/v1/screenshot \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://stripe.com",
    "viewport": {"width": 1920, "height": 1080},
    "auto_dismiss_modals": true,
    "s3_upload": true
  }'
```

---

## 🌐 1-Click Deployment (GitHub Pages)

1. Go to repository **Settings > Pages**.
2. Select branch `main`, folder `/ (root)`, and click **Save**.
3. Live application: **`https://jigyasha1712.github.io/Dynamic-Screenshot-API-Microservice/`**

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
