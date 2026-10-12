#!/usr/bin/env python3
"""
Multi-Portal Exam Announcements Scraper
Supports:
  1. NEET (UG) - https://neet.nta.nic.in/
  2. GATE 2027 - https://gate2027.iitm.ac.in/
"""

import copy
import json
import re
import sys
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_neet():
    """Scrapes announcements from the NEET (UG) NTA portal."""
    url = "https://neet.nta.nic.in/"
    print(f"[*] Fetching NEET announcements from {url}...")
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[!] Error fetching NEET: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    announcements = []
    seen = set()

    for a_tag in soup.select(".newsticker li a, .newsticker a"):
        title = a_tag.get_text(strip=True)
        href = a_tag.get("href", "").strip()
        if not title or not href or href.startswith("#"):
            continue
        link = urljoin(url, href)
        if link not in seen:
            seen.add(link)
            announcements.append({
                "exam": "NEET (UG)",
                "category": "Latest News (Ticker)",
                "title": title,
                "url": link,
            })

    for panel in soup.select(".vc_tta-panel"):
        heading_el = panel.select_one(".vc_tta-title-text")
        cat_name = heading_el.get_text(strip=True) if heading_el else "Public Notice"
        list_container = panel.select_one(".gen-list")
        if not list_container:
            continue

        for a_tag in list_container.find_all("a"):
            title = a_tag.get_text(strip=True)
            href = a_tag.get("href", "").strip()
            if not title or not href or href.startswith("#") or "view more" in title.lower():
                continue
            link = urljoin(url, href)
            if link not in seen:
                seen.add(link)
                announcements.append({
                    "exam": "NEET (UG)",
                    "category": cat_name,
                    "title": title,
                    "url": link,
                })

    return announcements


def scrape_gate():
    """Scrapes announcements, live ticker notices, and key dates from GATE 2027 portal."""
    base_url = "https://gate2027.iitm.ac.in/"
    announcements = []
    seen = set()

    # 1. Fetch live ticker notices from homepage
    print(f"[*] Fetching GATE 2027 live ticker notices from {base_url}...")
    try:
        r = requests.get(base_url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            track = soup.select_one(".notif-ticker")
            if track:
                for nb in track.find_all(class_="new-badge"):
                    nb.decompose()
                for sep in track.find_all(class_="ticker-sep"):
                    sep.replace_with("|||")
                raw_text = track.get_text(separator=" ", strip=True)
                for item in raw_text.split("|||"):
                    cleaned = re.sub(r"\s+", " ", item).strip()
                    cleaned = re.sub(r"(\d+)\s+(st|nd|rd|th)\b", r"\1\2", cleaned)
                    if cleaned and cleaned not in seen and len(cleaned) > 10:
                        seen.add(cleaned)
                        announcements.append({
                            "exam": "GATE 2027",
                            "category": "Latest News (Ticker)",
                            "title": cleaned,
                            "url": base_url,
                        })
    except requests.RequestException as e:
        print(f"[!] Error fetching GATE home ticker: {e}")

    # 2. Fetch document notifications
    notif_url = urljoin(base_url, "notifications")
    print(f"[*] Fetching GATE 2027 notifications from {notif_url}...")
    try:
        r = requests.get(notif_url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a"):
                title = a.get_text(strip=True)
                href = a.get("href", "").strip()
                if (
                    title
                    and href
                    and not href.startswith("#")
                    and (
                        ".pdf" in href.lower()
                        or any(k in title.lower() for k in ["notification", "issue", "admit", "result", "registration"])
                    )
                ):
                    link = urljoin(base_url, href)
                    if link not in seen:
                        seen.add(link)
                        announcements.append({
                            "exam": "GATE 2027",
                            "category": "Notification / Document",
                            "title": title,
                            "url": link,
                        })
    except requests.RequestException as e:
        print(f"[!] Error fetching GATE notifications: {e}")

    # 3. Fetch important dates
    dates_url = urljoin(base_url, "important_dates")
    print(f"[*] Fetching GATE 2027 dates from {dates_url}...")
    try:
        r = requests.get(dates_url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            current_activity = ""
            for tr in soup.select("table tr"):
                tds = tr.find_all(["td", "th"])
                if not tds or tds[0].name == "th":
                    continue
                if len(tds) == 3:
                    current_activity = re.sub(r"\s+", " ", tds[0].get_text(separator=" ", strip=True)).strip()
                    date_td = copy.copy(tds[1])
                elif len(tds) == 2:
                    t0 = re.sub(r"\s+", " ", tds[0].get_text(separator=" ", strip=True)).strip()
                    if "exam" in current_activity.lower():
                        date_td = copy.copy(tds[0])
                    else:
                        current_activity = t0
                        date_td = copy.copy(tds[1])
                else:
                    continue

                for d in date_td.find_all("del"):
                    d.decompose()
                date_val = re.sub(r"\s+", " ", date_td.get_text(separator=" ", strip=True)).strip()
                date_val = re.sub(r"(\d+)\s+(st|nd|rd|th)\b", r"\1\2", date_val)
                current_activity = re.sub(r"(\d+)\s+(st|nd|rd|th)\b", r"\1\2", current_activity)

                if date_val and date_val.lower() not in ("day", "saturday sunday"):
                    title_text = f"{current_activity} — {date_val}"
                    if title_text not in seen:
                        seen.add(title_text)
                        announcements.append({
                            "exam": "GATE 2027",
                            "category": "Important Dates",
                            "title": title_text,
                            "url": dates_url,
                        })
    except requests.RequestException as e:
        print(f"[!] Error fetching GATE dates: {e}")

    return announcements


def fetch_all(selected_site="all"):
    all_results = []
    if selected_site in ("all", "neet"):
        all_results.extend(scrape_neet())
    if selected_site in ("all", "gate"):
        all_results.extend(scrape_gate())
    return all_results


def main():
    selected_site = "all"
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("neet", "gate", "all"):
            selected_site = arg

    results = fetch_all(selected_site)

    # Normalize whitespace across all titles
    for r in results:
        r["title"] = re.sub(r'\s+', ' ', r["title"]).strip()

    print(f"\n[+] Total retrieved announcements: {len(results)}\n")
    for idx, item in enumerate(results[:10], 1):
        print(f"[{idx:02d}] [{item['exam']} | {item['category']}]")
        print(f"     Title: {item['title']}")
        print(f"     URL  : {item['url']}\n")
    if len(results) > 10:
        print(f"... and {len(results) - 10} more.")

    # Save to announcements.json
    output_file = "announcements.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[*] Saved announcements to {output_file}")

    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html = f.read()
        pattern = r"window\.__FALLBACK_DATA__\s*=\s*\[.*?\];"
        data_json = json.dumps(results, ensure_ascii=False)
        new_html = re.sub(pattern, lambda m: f"window.__FALLBACK_DATA__ = {data_json};", html, flags=re.DOTALL)
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(new_html)
        print("[*] Synchronized data in index.html")
    except Exception as e:
        pass


if __name__ == "__main__":
    main()
