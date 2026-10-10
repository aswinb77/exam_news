#!/usr/bin/env python3
"""
Multi-Portal Exam Announcements Scraper
Supports:
  1. NEET (UG) - https://neet.nta.nic.in/
  2. GATE 2027 - https://gate2027.iitm.ac.in/
"""

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
    """Scrapes announcements and key dates from GATE 2027 portal."""
    base_url = "https://gate2027.iitm.ac.in/"
    announcements = []
    seen = set()

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

    dates_url = urljoin(base_url, "important_dates")
    print(f"[*] Fetching GATE 2027 dates from {dates_url}...")
    try:
        r = requests.get(dates_url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for tr in soup.select("table tr"):
                cols = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if len(cols) >= 2 and cols[0] != "Activity":
                    activity = re.sub(r'\s+', ' ', cols[0]).strip()
                    date_val = re.sub(r'\s+', ' ', cols[1]).strip()
                    announcements.append({
                        "exam": "GATE 2027",
                        "category": "Important Dates",
                        "title": f"{activity} — {date_val}",
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
