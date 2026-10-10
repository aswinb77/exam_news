# Exam News & Alerts 📢

Get the latest news, notices, and updates from across various public examination portals in one unified dashboard.

![Live Web Dashboard](https://img.shields.io/badge/status-active-success.svg)
![Python 3](https://img.shields.io/badge/python-3.8+-blue.svg)

## 🌟 Features

- **Automated Web Scraping (`scrpe.py`)**: Fetches official circulars and notices from supported exam portals:
  - **NEET (UG)** (NTA Portal)
  - **GATE 2027** (IIT Madras Portal)
- **Interactive Web App (`index.html`)**:
  - Live search across exam titles, dates, and portals
  - Filter by portal / exam type
  - Sort by latest date or alphabetically
  - Spotlight hero card for the newest announcements
  - Responsive, modern Tailwind UI
- **Structured Data (`announcements.json`)**: Scraped notices stored in a lightweight JSON format for easy ingestion.
- **Automated Cloud Scheduling**: GitHub Actions workflow runs every 6 hours automatically to fetch new updates and keep the dashboard refreshed without keeping your computer on.

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have Python 3 installed with the required dependencies:
```bash
pip install requests beautifulsoup4
```

### 2. Run the Scraper
To scrape the latest notifications from the official portals and update `announcements.json`:
```bash
python3 scrpe.py
```

### 3. View the Web Dashboard
Open `index.html` in your web browser:
```bash
# On macOS
open index.html

# Or run a lightweight local server
python3 -m http.server 8000
```
Then visit `http://localhost:8000`.

## 🌐 Live Site
This project can be hosted directly via GitHub Pages:
[https://aswinb77.github.io/exam_news/](https://aswinb77.github.io/exam_news/)

## 📄 License
MIT License
