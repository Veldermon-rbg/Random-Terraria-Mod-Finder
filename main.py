import requests
from bs4 import BeautifulSoup
import random
import threading
import time
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import io
import os

# --- Config ---
APP_ID = 1281930
max_page = 1

# Paths
CHROME_DRIVER_PATH = r"C:\cd\chromedriver.exe"  # Your chromedriver.exe
CHROME_BINARY_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROME_PROFILE_PATH = r"C:\selenium_steam_profile"  # persistent Selenium profile
os.makedirs(CHROME_PROFILE_PATH, exist_ok=True)

# --- Selenium ---
chrome_options = Options()
chrome_options.binary_location = CHROME_BINARY_PATH
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")

# --- Functions ---
def update_max_page():
    global max_page
    while True:
        try:
            url = f"https://steamcommunity.com/workshop/browse/?appid={APP_ID}&browse"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            paging_div = soup.find("div", class_="workshopBrowsePagingControls")
            if paging_div:
                page_links = paging_div.find_all("a", class_="pagelink")
                page_numbers = []
                for a in page_links:
                    try:
                        num = int(a.text.strip())
                        page_numbers.append(num)
                    except:
                        continue
                if page_numbers:
                    max_page = max(page_numbers)
            print(f"[INFO] Max page updated: {max_page}")
        except Exception as e:
            print(f"[ERROR] Failed to update max page: {e}")
        time.sleep(120)

def fetch_random_mod():
    global max_page
    page = random.randint(1, max_page)
    url = f"https://steamcommunity.com/workshop/browse/?appid={APP_ID}&browse&p={page}"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.find_all("div", class_="workshopItem")
    if not items:
        return None
    item = random.choice(items)

    title_div = item.find("div", class_="workshopItemTitle")
    title = title_div.get_text(strip=True) if title_div else "Unknown"

    link_a = item.find("a", class_="ugc") or item.find("a", class_="item_link")
    link = link_a["href"] if link_a else None

    img_tag = item.find("img", class_="workshopItemPreviewImage")
    img_url = img_tag["src"] if img_tag else None

    author_div = item.find("div", class_="workshopItemAuthorName")
    author = author_div.get_text(strip=True) if author_div else "Unknown"

    return {"title": title, "link": link, "img_url": img_url, "author": author}

def open_and_subscribe(mod):
    if not mod or not mod["link"]:
        return
    try:
        wid = mod["link"].split("id=")[1].split("&")[0]
        driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=chrome_options)
        driver.get(mod["link"])
        time.sleep(3)
        driver.execute_script(f"SubscribeItem('{wid}', '{APP_ID}');")
        print(f"[INFO] Subscribed to {wid}")
    except Exception as e:
        print(f"[ERROR] Selenium failed: {e}")

def show_random_mod():
    mod = fetch_random_mod()
    if not mod:
        title_label.config(text="No mod found.")
        author_label.config(text="")
        image_label.config(image='')
        return

    # Scale font size based on title length for readability
    title_len = len(mod["title"])
    font_size = 16 if title_len < 40 else max(12, 16 - ((title_len - 40) // 5))
    title_label.config(text=mod["title"], font=("Arial", font_size, "bold"))
    author_label.config(text=f"Author: {mod['author']}")

    subscribe_button.config(command=lambda: open_and_subscribe(mod))

    if mod["img_url"]:
        try:
            img_data = requests.get(mod["img_url"]).content
            img = Image.open(io.BytesIO(img_data))
            img = img.resize((300, 300))
            photo = ImageTk.PhotoImage(img)
            image_label.config(image=photo)
            image_label.image = photo
        except:
            image_label.config(image='')
    else:
        image_label.config(image='')

# --- GUI ---
root = tk.Tk()
root.title("Random Mod Fetcher")
root.geometry("450x550")
root.configure(bg="#f0f0f0")  # light gray background

# Style
style = ttk.Style(root)
style.configure("TButton", font=("Arial", 14, "bold"), padding=6)
style.configure("TLabel", font=("Arial", 12), background="#f0f0f0", foreground="#000000")

main_frame = ttk.Frame(root, padding=10)
main_frame.pack(expand=True, fill=tk.BOTH)

title_label = ttk.Label(main_frame, text="Click this thingy", wraplength=400, font=("Arial", 16, "bold"), foreground="#1a1a1a")
title_label.pack(pady=10)

author_label = ttk.Label(main_frame, text="", font=("Arial", 14, "italic"), foreground="#333333")
author_label.pack(pady=5)

image_label = ttk.Label(main_frame)
image_label.pack(pady=10)

fetch_button = ttk.Button(main_frame, text="Get Random Mod", command=show_random_mod)
fetch_button.pack(pady=10, ipadx=10, ipady=5)

subscribe_button = ttk.Button(main_frame, text="Subscribe")
subscribe_button.pack(pady=5, ipadx=10, ipady=5)

# Start background thread
threading.Thread(target=update_max_page, daemon=True).start()

root.mainloop()
