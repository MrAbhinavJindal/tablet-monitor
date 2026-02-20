import customtkinter as ctk
from datetime import datetime, timedelta
import pytz
import requests
from screeninfo import get_monitors
import psutil
import threading
import subprocess
import os
import sys
import ctypes
from PIL import Image, ImageTk
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import win32com.client
import tkinter as tk

# Disable CustomTkinter DPI scaling to fix Python 3.13 compatibility
ctk.deactivate_automatic_dpi_awareness()

# Set CustomTkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ================= CONFIG =================
API_KEY = "44165a92e62c4373a3f221f36c33b921"
CITIES = {
    "IST": ("Bangalore", "Asia/Kolkata"),
    "CH": ("Zurich", "Europe/Zurich"),
    "UK": ("London", "Europe/London")
}
# Modern gradient color scheme
BG_GRADIENT_START = "#0f0c29"
BG_GRADIENT_MID = "#302b63" 
BG_GRADIENT_END = "#24243e"
CARD_BG = "#1e1e2e"
CARD_BORDER = "#2d2d44"
ACCENT_PRIMARY = "#00d4ff"
ACCENT_SECONDARY = "#7b2cbf"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#b4b4c5"
FONT_TIME = ("Segoe UI", 32, "bold")
FONT_ZONE = ("Segoe UI", 16)
FONT_CARD_TITLE = ("Segoe UI", 18, "bold")
FONT_CARD_TEXT = ("Segoe UI", 14)
ATTENDANCE_RETRY_MS = 1800000
NOTES_FILE = "mynotes.txt"
DAILY_DATA_FILE = "daily_data.json"

def create_gradient_bg(canvas, width, height):
    """Create a gradient background on canvas"""
    colors = [BG_GRADIENT_START, BG_GRADIENT_MID, BG_GRADIENT_END]
    steps = height
    for i in range(steps):
        ratio = i / steps
        if ratio < 0.5:
            r1, g1, b1 = int(colors[0][1:3], 16), int(colors[0][3:5], 16), int(colors[0][5:7], 16)
            r2, g2, b2 = int(colors[1][1:3], 16), int(colors[1][3:5], 16), int(colors[1][5:7], 16)
            ratio = ratio * 2
        else:
            r1, g1, b1 = int(colors[1][1:3], 16), int(colors[1][3:5], 16), int(colors[1][5:7], 16)
            r2, g2, b2 = int(colors[2][1:3], 16), int(colors[2][3:5], 16), int(colors[2][5:7], 16)
            ratio = (ratio - 0.5) * 2
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        color = f'#{r:02x}{g:02x}{b:02x}'
        canvas.create_line(0, i, width, i, fill=color, width=1)

def create_card_frame(parent, title=None):
    """Create a modern card-style frame with rounded corners using CustomTkinter"""
    card = ctk.CTkFrame(parent, fg_color=CARD_BG, border_color=CARD_BORDER, border_width=2, corner_radius=15)
    if title:
        title_label = ctk.CTkLabel(card, text=title, text_color=ACCENT_PRIMARY, font=("Segoe UI", 23, "bold"))
        title_label.pack(anchor="w", padx=26, pady=(20, 13))
    return card

# -------- FUNCTIONS --------
def get_my_location():
    try:
        r = requests.get("https://ip-api.com/json", timeout=5).json()
        return r["lat"], r["lon"]
    except Exception:
        return None, None

def get_weather_current_location():
    try:
        # Use fixed coordinates for accurate weather
        lat, lon = 28.6106, 77.4576
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        r = requests.get(url, timeout=5).json()
        temp = round(r["main"]["temp"])
        desc = r["weather"][0]["main"]
        return f"{temp}°C {desc}"
    except Exception:
        return "--"

def get_battery():
    try:
        b = psutil.sensors_battery()
        if not b:
            return "--"
        icon = "⚡" if b.power_plugged else "🔋"
        return f"{b.percent:.0f}%"
    except Exception:
        return "--"

def fetch_attendance_time():
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--silent")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        service = Service("chromedriver.exe", log_path='NUL')
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 15)
        driver.get("https://contevolve.greythr.com/uas/portal/auth/login")
        wait.until(EC.visibility_of_element_located((By.NAME, "username")))
        driver.find_element(By.NAME, "username").send_keys("CV0005")
        driver.find_element(By.NAME, "password").send_keys("Trapeze2023q1@")
        driver.find_element(By.XPATH, '/html/body/app-root/uas-portal/div/div/main/div/section/div[1]/o-auth/section/div/app-login/section/div/div/div/form/div[4]/button').click()
        wait.until(EC.visibility_of_element_located((By.XPATH, '/html/body/app/ng-component/div/div/div[2]/div/ghr-home/div')))
        driver.execute_script("window.open('https://contevolve.greythr.com/v3/portal/ess/attendance/attendance-info', '_blank');")
        driver.switch_to.window(driver.window_handles[1])
        wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/app/ng-component/div/div/div[2]/div/gt-attendance-info-calendar/div[1]/div[2]/div[2]/div/div[4]/accordion/accordion-group/div/div[1]/div/div/div'))).click()
        raw_time = driver.find_element(By.XPATH, '/html/body/app/ng-component/div/div/div[2]/div/gt-attendance-info-calendar/div[1]/div[2]/div[2]/div/div[4]/accordion/accordion-group/div/div[2]/div/table[1]/tbody/tr/td[1]/p[1]').text.strip().upper()
        t = datetime.strptime(raw_time, "%I:%M:%S %p") + timedelta(hours=9)
        return t.strftime("%I:%M %p")
    except Exception:
        return "--"
    finally:
        if driver:
            driver.quit()

def load_notes():
    try:
        if os.path.exists(NOTES_FILE):
            with open(NOTES_FILE, 'r', encoding='utf-8') as f:
                return f.read()
        return "Start typing your notes here..."
    except Exception:
        return "Start typing your notes here..."

def save_notes():
    try:
        content = notes_text.get("1.0", "end-1c")
        with open(NOTES_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception:
        pass

def on_text_change(event=None):
    save_notes()

def get_daily_inspiration():
    import json
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        if os.path.exists(DAILY_DATA_FILE):
            with open(DAILY_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('date') == today:
                    return data.get('quote', 'Stay positive and keep growing!'), data.get('word', 'Resilience'), data.get('meaning', 'The ability to recover quickly from difficulties'), data.get('sentence', 'Her resilience helped her overcome every challenge.')
    except Exception:
        pass
    
    # Fallback quotes and words
    quotes = [
        "Success is not final, failure is not fatal: it is the courage to continue that counts.",
        "The only way to do great work is to love what you do.",
        "Innovation distinguishes between a leader and a follower.",
        "Your limitation—it's only your imagination.",
        "Push yourself, because no one else is going to do it for you."
    ]
    
    words_data = [
        ("Serendipity", "A pleasant surprise or fortunate accident", "Finding this job was pure serendipity."),
        ("Resilience", "The ability to recover quickly from difficulties", "Her resilience helped her overcome every challenge."),
        ("Eloquent", "Fluent and persuasive in speaking or writing", "His eloquent speech moved the entire audience."),
        ("Perseverance", "Persistence in doing something despite difficulty", "Success requires perseverance and dedication."),
        ("Innovative", "Featuring new methods; advanced and original", "The company's innovative approach revolutionized the industry.")
    ]
    
    import random
    quote = random.choice(quotes)
    word, meaning, sentence = random.choice(words_data)
    
    # Save today's data
    try:
        daily_data = {
            'date': today,
            'quote': quote,
            'word': word,
            'meaning': meaning,
            'sentence': sentence
        }
        with open(DAILY_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(daily_data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    
    return quote, word, meaning, sentence

def get_outlook_events():
    outlook = win32com.client.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")
    calendar = namespace.GetDefaultFolder(9)
    appointments = calendar.Items
    appointments.Sort("[Start]")
    appointments.IncludeRecurrences = True
    
    today = datetime.now().date()
    week_end = today + timedelta(days=2)
    events = []
    for item in appointments:
        try:
            item_start = item.Start.date() if hasattr(item.Start, 'date') else None
            if item_start and today <= item_start <= week_end:
                start_time = item.Start.strftime('%I:%M %p') if hasattr(item.Start, 'strftime') else str(item.Start)
                end_time = item.End.strftime('%I:%M %p') if hasattr(item.End, 'strftime') else str(item.End)
                events.append({
                    'subject': item.Subject,
                    'start': start_time,
                    'end': end_time,
                    'date': item_start.strftime('%a %d'),
                    'full_date': item_start,
                    'end_datetime': item.End,
                    'location': item.Location
                })
                if len(events) >= 10:
                    break
        except:
            pass
    return events


def toggle_microphone():
    global mike_muted
    mike_muted = not mike_muted
    threading.Thread(target=_toggle_mic_thread, daemon=True).start()
    update_mike_button()

def _toggle_mic_thread():
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetMicrophone()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMute(1 if mike_muted else 0, None)
    except Exception:
        pass

def set_volume(val):
    global volume_timer
    if volume_timer:
        root.after_cancel(volume_timer)
    volume_timer = root.after(50, lambda: threading.Thread(target=_set_volume_thread, args=(val,), daemon=True).start())

def _set_volume_thread(val):
    try:
        subprocess.Popen(["nircmd", "setsysvolume", str(int(float(val) * 655.35))], shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def update_mike_button():
    if mic_photo:
        if mike_muted:
            mike_label.config(image=mic_photo_muted)
        else:
            mike_label.config(image=mic_photo)
    else:
        if mike_muted:
            mike_label.config(text="🔇")
        else:
            mike_label.config(text="🎤")

def blynk_button_click():
    threading.Thread(target=lambda: requests.get("http://blynk.tk:8080/65FhSzpi6hJApqWPwsH-IIrY_8k2BV4K/update/V0?value=4", timeout=5), daemon=True).start()

def blynk_slider_release(event):
    val = blynk_slider.get()
    threading.Thread(target=lambda: requests.get(f"http://blynk.tk:8080/65FhSzpi6hJApqWPwsH-IIrY_8k2BV4K/update/V1?value={int(val)}", timeout=5), daemon=True).start()

def show_paint_screen():
    paint_window = tk.Toplevel(root)
    paint_window.overrideredirect(True)
    paint_window.configure(bg="black")
    paint_window.geometry(f"{width}x{height}+{x}+{y}")
    paint_window.attributes("-topmost", True)
    
    current_color = "white"
    show_palette = False
    
    canvas = tk.Canvas(paint_window, bg="black", highlightthickness=0, bd=0)
    canvas.pack(fill="both", expand=True)
    
    palette_frame = tk.Frame(paint_window, bg="black", padx=15, pady=10)
    colors = ["#FFFFFF", "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF", "#FFA500", "#800080", "#FFC0CB"]
    
    def select_color(color):
        nonlocal current_color
        current_color = color
        toggle_palette()
    
    for i, color in enumerate(colors):
        color_canvas = tk.Canvas(palette_frame, width=60, height=60, bg="black", highlightthickness=0, bd=0)
        color_canvas.grid(row=0, column=i, padx=8, pady=10)
        color_canvas.create_oval(10, 10, 50, 50, fill=color, outline="white", width=2)
        color_canvas.bind("<Button-1>", lambda e, c=color: select_color(c))
    
    def toggle_palette():
        nonlocal show_palette
        if show_palette:
            palette_frame.pack_forget()
            show_palette = False
        else:
            palette_frame.pack(side="top", pady=10)
            show_palette = True
    
    options_frame = tk.Frame(paint_window, bg="black")
    options_frame.pack(side="bottom", pady=15)
    
    def save_drawing():
        try:
            if not os.path.exists("Drawings"):
                os.makedirs("Drawings")
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join("Drawings", f"{timestamp}.png")
            from PIL import Image, ImageDraw
            canvas.update()
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            img = Image.new('RGB', (w, h), 'black')
            draw = ImageDraw.Draw(img)
            for item in canvas.find_all():
                coords = canvas.coords(item)
                if canvas.type(item) == 'line' and len(coords) >= 4:
                    for i in range(0, len(coords)-2, 2):
                        x1, y1 = coords[i], coords[i+1]
                        x2, y2 = coords[i+2], coords[i+3]
                        color = canvas.itemcget(item, 'fill')
                        width_val = int(float(canvas.itemcget(item, 'width')))
                        for offset in range(-width_val//2, width_val//2 + 1):
                            draw.line([(x1+offset, y1), (x2+offset, y2)], fill=color)
                            draw.line([(x1, y1+offset), (x2, y2+offset)], fill=color)
            img.save(filename, "PNG")
            saved_label = tk.Label(paint_window, text="Saved!", fg="#4CAF50", bg="black", font=("Segoe UI", 16, "bold"))
            saved_label.place(relx=0.5, rely=0.1, anchor="center")
            paint_window.after(2000, saved_label.destroy)
        except Exception:
            pass
    
    if new_photo:
        tk.Button(options_frame, image=new_photo, bg="black", bd=0, relief="flat", command=lambda: canvas.delete("all")).pack(side="left", padx=15)
    else:
        tk.Button(options_frame, text="📄", bg="black", fg="white", font=("Segoe UI", 24), bd=0, relief="flat", command=lambda: canvas.delete("all")).pack(side="left", padx=15)
    
    if save_photo:
        tk.Button(options_frame, image=save_photo, bg="black", bd=0, relief="flat", command=save_drawing).pack(side="left", padx=15)
    else:
        tk.Button(options_frame, text="💾", bg="black", fg="white", font=("Segoe UI", 24), bd=0, relief="flat", command=save_drawing).pack(side="left", padx=15)
    
    if colors_photo:
        tk.Button(options_frame, image=colors_photo, bg="black", bd=0, relief="flat", command=toggle_palette).pack(side="left", padx=15)
    else:
        tk.Button(options_frame, text="🎨", bg="black", fg="white", font=("Segoe UI", 24), bd=0, relief="flat", command=toggle_palette).pack(side="left", padx=15)
    
    if back_photo:
        tk.Button(options_frame, image=back_photo, bg="black", bd=0, relief="flat", command=paint_window.destroy).pack(side="left", padx=15)
    else:
        tk.Button(options_frame, text="◀", bg="black", fg="white", font=("Segoe UI", 24), bd=0, relief="flat", command=paint_window.destroy).pack(side="left", padx=15)
    
    last_x, last_y = None, None
    
    def paint(event):
        nonlocal last_x, last_y
        if last_x and last_y:
            canvas.create_line(last_x, last_y, event.x, event.y, fill=current_color, width=6, capstyle=tk.ROUND, smooth=True)
        last_x, last_y = event.x, event.y
    
    def start_paint(event):
        nonlocal last_x, last_y
        last_x, last_y = event.x, event.y
    
    def stop_paint(event):
        nonlocal last_x, last_y
        last_x, last_y = None, None
    
    canvas.bind("<Button-1>", start_paint)
    canvas.bind("<B1-Motion>", paint)
    canvas.bind("<ButtonRelease-1>", stop_paint)

# -------- SETUP --------
def get_secondary_monitor():
    """Get secondary monitor with retry logic for SpaceDesk reconnection"""
    for attempt in range(30):  # Try for 30 seconds
        try:
            monitors = get_monitors()
            secondaries = [m for m in monitors if not m.is_primary]
            if secondaries:
                # Check for 1080x1920 resolution or 864x1536 (125% scaling)
                for m in secondaries:
                    if (m.width == 1080 and m.height == 1920) or (m.width == 864 and m.height == 1536):
                        return m
                # If no matching resolution found, return None to exit
                return None
        except Exception:
            pass
        if attempt < 29:
            import time
            time.sleep(1)
    return None

smaller_monitor = get_secondary_monitor()
if not smaller_monitor:
    print("No monitor with 1080x1920 or 864x1536 resolution found. Exiting.")
    sys.exit(0)
else:
    print(f"Using secondary monitor: {smaller_monitor.width}x{smaller_monitor.height}")

x, y = smaller_monitor.x, smaller_monitor.y
width, height = smaller_monitor.width, smaller_monitor.height

root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-transparentcolor", "black")
root.configure(bg="black")
root.geometry(f"{width}x{height}+{x}+{y}")

# Remove gradient background - use transparent instead
# bg_canvas = tk.Canvas(root, width=width, height=height, highlightthickness=0)
# bg_canvas.pack(fill="both", expand=True)
# create_gradient_bg(bg_canvas, width, height)

# Main container directly on root with transparent background
main_container = tk.Frame(root, bg="black")
main_container.pack(fill="both", expand=True)





def update_calendar():
    def fetch_and_update():
        import pythoncom
        pythoncom.CoInitialize()
        try:
            print("Fetching Outlook events...")
            events = get_outlook_events()
            print(f"Found {len(events)} events")
            for event in events:
                print(f"  - {event['date']} {event['start']}-{event['end']}: {event['subject']}")
            root.after(0, lambda: display_events(events))
        finally:
            pythoncom.CoUninitialize()
    
    def display_events(events):
        print(f"Displaying {len(events)} events in UI")
        for widget in calendar_list.winfo_children():
            widget.destroy()
        
        now = datetime.now()
        today = now.date()
        print(f"Current time: {now}")
        print(f"Today's date: {today}")
        if events:
            for event in events[:10]:
                try:
                    event_date = event['full_date']
                    event_end = event['end_datetime']
                    # Remove timezone info to compare with naive datetime
                    if hasattr(event_end, 'replace'):
                        event_end = event_end.replace(tzinfo=None)
                    is_past = event_end < now and event_date == today
                    print(f"Event: {event['subject'][:30]} | End: {event_end} | Is Past: {is_past} | Date Match: {event_date == today}")
                except Exception as e:
                    print(f"Error parsing event: {e}")
                    is_past = False
                
                bg_color = "#1a1520" if is_past else CARD_BG
                fg_time = "#666666" if is_past else ACCENT_PRIMARY
                fg_subject = "#555555" if is_past else TEXT_PRIMARY
                fg_location = "#444444" if is_past else TEXT_SECONDARY
                
                event_frame = ctk.CTkFrame(calendar_list, fg_color=bg_color, border_color=CARD_BORDER, border_width=1, corner_radius=10)
                event_frame.pack(fill="x", pady=3, padx=0, expand=True)
                
                date_time = ctk.CTkLabel(event_frame, text=f"{event['date']} | {event['start']} - {event['end']}", text_color=fg_time, font=("Segoe UI", 18, "bold"))
                date_time.pack(anchor="w", padx=20, pady=(16, 4))
                
                subject_label = ctk.CTkLabel(event_frame, text=event['subject'], text_color=fg_subject, font=("Segoe UI", 21), wraplength=676, justify="left")
                subject_label.pack(anchor="w", padx=20, pady=(0, 4))
                
                if event.get('location'):
                    location_label = ctk.CTkLabel(event_frame, text=f"📍 {event['location']}", text_color=fg_location, font=("Segoe UI", 17), wraplength=676, justify="left")
                    location_label.pack(anchor="w", padx=20, pady=(0, 16))
            print("Events displayed successfully")
        else:
            no_events = ctk.CTkLabel(calendar_list, text="No meetings in next 2 days", text_color=TEXT_SECONDARY, font=("Segoe UI", 23, "italic"))
            no_events.pack(pady=26)
            print("No events message displayed")
        
        root.after(600000, update_calendar)
    
    threading.Thread(target=fetch_and_update, daemon=True).start()

# Top section with inspiration - 2 cards side by side
top_section = tk.Frame(main_container, bg="black")
top_section.pack(side="top", fill="x", padx=26, pady=(20, 7))

quote, word, meaning, sentence = get_daily_inspiration()

# Thought of the day card (left)
thought_card = create_card_frame(top_section, "💭 Thought of the Day")
thought_card.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=5)

quote_label = ctk.CTkLabel(thought_card, text=f'"{quote}"', text_color=TEXT_PRIMARY, font=("Segoe UI", 23, "italic"), wraplength=520, justify="center")
quote_label.pack(pady=(13, 20), padx=26)

# Word of the day card (right)
word_card = create_card_frame(top_section, "📚 Word of the Day")
word_card.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=5)

word_label = ctk.CTkLabel(word_card, text=f"💡 {word}", text_color=ACCENT_PRIMARY, font=("Segoe UI", 26, "bold"))
word_label.pack(pady=(13, 7))

meaning_label = ctk.CTkLabel(word_card, text=meaning, text_color=TEXT_SECONDARY, font=("Segoe UI", 21, "bold"), wraplength=455, justify="center")
meaning_label.pack(pady=(0, 7))

sentence_label = ctk.CTkLabel(word_card, text=f'"{sentence}"', text_color=TEXT_SECONDARY, font=("Segoe UI", 18, "italic"), wraplength=455, justify="center")
sentence_label.pack(pady=(0, 20))

# Clock section
clock_section = tk.Frame(main_container, bg="black")
clock_section.pack(side="top", pady=5)

clock_labels = {}
for zone in CITIES:
    zone_card = create_card_frame(clock_section)
    zone_card.pack(side="left", padx=8)
    
    zone_label = ctk.CTkLabel(zone_card, text=zone, text_color=TEXT_SECONDARY, font=("Segoe UI", 21))
    zone_label.pack(padx=26, pady=(13, 7))
    
    time_label = ctk.CTkLabel(zone_card, text="", text_color=ACCENT_PRIMARY, font=("Segoe UI", 42, "bold"))
    time_label.pack(padx=26, pady=(0, 13))
    
    clock_labels[zone] = time_label

# Load icons before creating UI elements that use them
mike_muted = False
volume_timer = None

try:
    paint_icon = Image.open("icons/paint.png").resize((64, 64), Image.Resampling.LANCZOS)
    paint_photo = ImageTk.PhotoImage(paint_icon)
    
    mic_icon = Image.open("icons/mic.png").resize((64, 64), Image.Resampling.LANCZOS)
    mic_photo = ImageTk.PhotoImage(mic_icon)
    
    mic_icon_muted = mic_icon.copy()
    mic_icon_muted.putalpha(128)
    mic_photo_muted = ImageTk.PhotoImage(mic_icon_muted)
    
    volume_icon = Image.open("icons/volume.png").resize((64, 64), Image.Resampling.LANCZOS)
    volume_photo = ImageTk.PhotoImage(volume_icon)
    
    brightness_icon = Image.open("icons/brightness.png").resize((64, 64), Image.Resampling.LANCZOS)
    brightness_photo = ImageTk.PhotoImage(brightness_icon)
    
    power_icon = Image.open("icons/power.png").resize((64, 64), Image.Resampling.LANCZOS)
    power_photo = ImageTk.PhotoImage(power_icon)
    
    new_icon = Image.open("icons/new.png").resize((96, 96), Image.Resampling.LANCZOS)
    new_photo = ImageTk.PhotoImage(new_icon)
    
    back_icon = Image.open("icons/back.png").resize((96, 96), Image.Resampling.LANCZOS)
    back_photo = ImageTk.PhotoImage(back_icon)
    
    save_icon = Image.open("icons/save.png").resize((96, 96), Image.Resampling.LANCZOS)
    save_photo = ImageTk.PhotoImage(save_icon)
    
    colors_icon = Image.open("icons/colors.png").resize((96, 96), Image.Resampling.LANCZOS)
    colors_photo = ImageTk.PhotoImage(colors_icon)
    
    clock_icon = Image.open("icons/clock.png").resize((48, 48), Image.Resampling.LANCZOS)
    clock_photo = ImageTk.PhotoImage(clock_icon)
    
    battery_icon = Image.open("icons/onbattery.png").resize((48, 48), Image.Resampling.LANCZOS)
    battery_photo = ImageTk.PhotoImage(battery_icon)
    
    weather_icon = Image.open("icons/weather.png").resize((48, 48), Image.Resampling.LANCZOS)
    weather_photo = ImageTk.PhotoImage(weather_icon)
    
    charging_icon = Image.open("icons/charging.png").resize((48, 48), Image.Resampling.LANCZOS)
    charging_photo = ImageTk.PhotoImage(charging_icon)
    
    onbattery_icon = Image.open("icons/onbattery.png").resize((48, 48), Image.Resampling.LANCZOS)
    onbattery_photo = ImageTk.PhotoImage(onbattery_icon)
except Exception:
    paint_photo = mic_photo = mic_photo_muted = volume_photo = brightness_photo = power_photo = new_photo = back_photo = save_photo = colors_photo = clock_photo = battery_photo = charging_photo = onbattery_photo = weather_photo = None

# Info cards section
info_section = tk.Frame(main_container, bg="black")
info_section.pack(side="top", pady=5)

# Battery card
battery_card = create_card_frame(info_section)
battery_card.pack(side="left", padx=8)
battery_icon_label = tk.Label(battery_card, bg=CARD_BG)
battery_icon_label.pack(side="left", padx=(10, 5), pady=8)
battery_label = tk.Label(battery_card, text="--", fg=TEXT_PRIMARY, bg=CARD_BG, font=("Segoe UI", 18, "bold"))
battery_label.pack(side="left", padx=(0, 13), pady=10)

# Weather card
weather_card = create_card_frame(info_section)
weather_card.pack(side="left", padx=8)
weather_icon_label = tk.Label(weather_card, bg=CARD_BG)
weather_icon_label.pack(side="left", padx=(10, 5), pady=8)
weather_label = tk.Label(weather_card, text="--", fg=TEXT_PRIMARY, bg=CARD_BG, font=("Segoe UI", 18, "bold"), wraplength=156)
weather_label.pack(side="left", padx=(0, 13), pady=10)

# Attendance card
attendance_card = create_card_frame(info_section)
attendance_card.pack(side="left", padx=8)
attendance_icon_label = tk.Label(attendance_card, bg=CARD_BG)
attendance_icon_label.pack(side="left", padx=(10, 5), pady=8)
attendance_label = tk.Label(attendance_card, text="--", fg=TEXT_PRIMARY, bg=CARD_BG, font=("Segoe UI", 18, "bold"))
attendance_label.pack(side="left", padx=(0, 13), pady=10)

# Bottom section with notes and calendar
bottom_section = tk.Frame(main_container, bg="black")
bottom_section.pack(side="top", fill="both", expand=True, padx=26, pady=13)

# Configure grid to split 50-50
bottom_section.grid_columnconfigure(0, weight=1, uniform="equal")
bottom_section.grid_columnconfigure(1, weight=1, uniform="equal")
bottom_section.grid_rowconfigure(0, weight=1)

# Notes card (left half)
notes_card = create_card_frame(bottom_section, "📝 My Notes")
notes_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

notes_text = tk.Text(notes_card, font=("Segoe UI", 21), wrap="word", bg="#252535", fg=TEXT_PRIMARY, bd=0, padx=26, pady=20, insertbackground=ACCENT_PRIMARY, relief="flat")
notes_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
notes_text.bind('<KeyRelease>', on_text_change)

# Calendar card (right half)
calendar_card = create_card_frame(bottom_section, "📅 Upcoming Meetings")
calendar_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

calendar_scroll_frame = tk.Frame(calendar_card, bg=CARD_BG)
calendar_scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

calendar_canvas = tk.Canvas(calendar_scroll_frame, bg=CARD_BG, highlightthickness=0)
calendar_list = tk.Frame(calendar_canvas, bg=CARD_BG)

calendar_canvas.create_window((0, 0), window=calendar_list, anchor="nw")

calendar_canvas.pack(fill="both", expand=True)

def on_calendar_configure(event):
    calendar_canvas.configure(scrollregion=calendar_canvas.bbox("all"))

def bind_mouse_scroll(widget):
    widget.bind("<Enter>", lambda e: calendar_canvas.bind_all("<MouseWheel>", on_mouse_wheel))
    widget.bind("<Leave>", lambda e: calendar_canvas.unbind_all("<MouseWheel>"))
    # Add touch scrolling support
    widget.bind("<Button-1>", start_scroll)
    widget.bind("<B1-Motion>", do_scroll)
    widget.bind("<ButtonRelease-1>", end_scroll)

def on_mouse_wheel(event):
    calendar_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

# Touch scrolling variables
scroll_start_y = 0
last_scroll_y = 0

def start_scroll(event):
    global scroll_start_y, last_scroll_y
    scroll_start_y = event.y_root
    last_scroll_y = event.y_root

def do_scroll(event):
    global last_scroll_y
    delta = last_scroll_y - event.y_root
    calendar_canvas.yview_scroll(int(delta/10), "units")
    last_scroll_y = event.y_root

def end_scroll(event):
    pass

calendar_list.bind("<Configure>", on_calendar_configure)
bind_mouse_scroll(calendar_canvas)
bind_mouse_scroll(calendar_list)

# Footer bar with paint and controls
footer = ctk.CTkFrame(root, fg_color=CARD_BG, border_color=CARD_BORDER, border_width=2, corner_radius=15, height=130)
footer.pack(side="bottom", fill="x", padx=26, pady=26)

# Paint button in footer
if paint_photo:
    paint_button = tk.Label(footer, image=paint_photo, bg=CARD_BG, cursor="hand2", bd=0)
else:
    paint_button = tk.Label(footer, text="🎨", fg=TEXT_PRIMARY, bg=CARD_BG, font=("Segoe UI", 32), cursor="hand2", bd=0)
paint_button.pack(side="left", padx=20, pady=20)
paint_button.bind("<Button-1>", lambda e: show_paint_screen())

# Controls in footer
controls_container = tk.Frame(footer, bg=CARD_BG)
controls_container.pack(side="right", padx=20, pady=15)

# Brightness control
brightness_frame = tk.Frame(controls_container, bg=CARD_BG)
brightness_frame.pack(side="left", padx=(0, 20))

if brightness_photo:
    tk.Label(brightness_frame, image=brightness_photo, bg=CARD_BG).pack(pady=(0, 5))
else:
    tk.Label(brightness_frame, text="☀️", fg=TEXT_PRIMARY, bg=CARD_BG, font=("Segoe UI", 24)).pack(pady=(0, 5))

blynk_slider = tk.Scale(brightness_frame, from_=255, to=0, orient="vertical", bg=CARD_BG, fg=ACCENT_PRIMARY, troughcolor="#2d2d44", activebackground=ACCENT_PRIMARY, highlightthickness=0, length=120, width=30, sliderlength=20, bd=0, showvalue=False)
blynk_slider.bind("<ButtonRelease-1>", blynk_slider_release)
blynk_slider.pack()

if power_photo:
    blynk_button = tk.Label(brightness_frame, image=power_photo, bg=CARD_BG, cursor="hand2", bd=0)
    blynk_button.pack(pady=(5, 0))
    blynk_button.bind("<Button-1>", lambda e: blynk_button_click())
else:
    blynk_button = tk.Button(brightness_frame, text="⏻", bg=ACCENT_PRIMARY, fg="#000000", font=("Segoe UI", 16, "bold"), command=blynk_button_click, bd=0, padx=10, pady=5, relief="flat", cursor="hand2")
    blynk_button.pack(pady=(5, 0))

# Volume control
volume_frame = tk.Frame(controls_container, bg=CARD_BG)
volume_frame.pack(side="left")

if volume_photo:
    tk.Label(volume_frame, image=volume_photo, bg=CARD_BG).pack(pady=(0, 5))
else:
    tk.Label(volume_frame, text="🔊", fg=TEXT_PRIMARY, bg=CARD_BG, font=("Segoe UI", 24)).pack(pady=(0, 5))

vol_slider = tk.Scale(volume_frame, from_=100, to=0, orient="vertical", bg=CARD_BG, fg=ACCENT_PRIMARY, troughcolor="#2d2d44", activebackground=ACCENT_PRIMARY, highlightthickness=0, command=set_volume, length=120, width=30, sliderlength=20, bd=0, showvalue=False)
vol_slider.set(50)
vol_slider.pack()

if mic_photo:
    mike_label = tk.Label(volume_frame, image=mic_photo, bg=CARD_BG, cursor="hand2", bd=0)
else:
    mike_label = tk.Label(volume_frame, text="🎤", fg=TEXT_PRIMARY, bg=CARD_BG, font=("Segoe UI", 20), cursor="hand2", bd=0)
mike_label.pack(pady=(5, 0))
mike_label.bind("<Button-1>", lambda e: toggle_microphone())
update_mike_button()

# -------- UPDATE --------
attendance_done = False
tz_cache = {zone: pytz.timezone(tz) for zone, (_, tz) in CITIES.items()}

def update_time():
    for zone in CITIES:
        now = datetime.now(tz_cache[zone])
        clock_labels[zone].configure(text=now.strftime('%I:%M:%S %p'))
    root.after(1000, update_time)

def update_right():
    battery_label.config(text=get_battery())
    try:
        b = psutil.sensors_battery()
        if b and charging_photo and onbattery_photo:
            battery_icon_label.config(image=charging_photo if b.power_plugged else onbattery_photo)
    except:
        pass
    if weather_photo:
        weather_icon_label.config(image=weather_photo)
    if clock_photo:
        attendance_icon_label.config(image=clock_photo)
    weather_label.config(text=get_weather_current_location())
    root.after(60000, update_right)

def update_attendance():
    global attendance_done
    def task():
        global attendance_done
        value = fetch_attendance_time()
        root.after(0, lambda: attendance_label.config(text=f"{value}"))
        if value != "--":
            attendance_done = True
        else:
            root.after(ATTENDANCE_RETRY_MS, update_attendance)
    if not attendance_done:
        threading.Thread(target=task, daemon=True).start()

# -------- START --------
notes_text.insert("1.0", load_notes())
update_time()
update_right()
update_attendance()
update_calendar()

# Handle window close gracefully
def on_closing():
    save_notes()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()