import customtkinter as ctk
from datetime import datetime, timedelta
import pytz, requests, psutil, threading, subprocess, os, sys, json, random
from screeninfo import get_monitors
from PIL import Image, ImageTk
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import win32com.client
import tkinter as tk

ctk.deactivate_automatic_dpi_awareness()
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

API_KEY = "44165a92e62c4373a3f221f36c33b921"
CITIES = {"IST": ("Bangalore", "Asia/Kolkata"), "CH": ("Zurich", "Europe/Zurich"), "UK": ("London", "Europe/London")}
CARD_BG, CARD_BORDER, ACCENT_PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY = "#1e1e2e", "#2d2d44", "#00d4ff", "#ffffff", "#b4b4c5"
ATTENDANCE_RETRY_MS, NOTES_FILE, DAILY_DATA_FILE = 1800000, "mynotes.txt", "daily_data.json"

def create_card_frame(parent, title=None):
    card = ctk.CTkFrame(parent, fg_color=CARD_BG, border_color=CARD_BORDER, border_width=2, corner_radius=15)
    if title:
        ctk.CTkLabel(card, text=title, text_color=ACCENT_PRIMARY, font=("Segoe UI", 23, "bold")).pack(anchor="w", padx=26, pady=(20, 13))
    return card

def get_weather_current_location():
    try:
        r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat=28.6106&lon=77.4576&appid={API_KEY}&units=metric", timeout=5).json()
        return f"{round(r['main']['temp'])}°C {r['weather'][0]['main']}"
    except:
        return "--"

def get_battery():
    try:
        b = psutil.sensors_battery()
        return f"{b.percent:.0f}%" if b else "--"
    except:
        return "--"

def fetch_attendance_time():
    try:
        opts = Options()
        for arg in ["--headless", "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage", "--log-level=3", "--silent"]:
            opts.add_argument(arg)
        opts.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = webdriver.Chrome(service=Service("chromedriver.exe", log_path='NUL'), options=opts)
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
        driver.quit()
        return t.strftime("%I:%M %p")
    except:
        return "--"

def load_notes():
    try:
        return open(NOTES_FILE, 'r', encoding='utf-8').read() if os.path.exists(NOTES_FILE) else "Start typing your notes here..."
    except:
        return "Start typing your notes here..."

def save_notes():
    try:
        open(NOTES_FILE, 'w', encoding='utf-8').write(notes_text.get("1.0", "end-1c"))
    except:
        pass

def get_daily_inspiration():
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        if os.path.exists(DAILY_DATA_FILE):
            data = json.load(open(DAILY_DATA_FILE, 'r', encoding='utf-8'))
            if data.get('date') == today:
                return data.get('quote'), data.get('word'), data.get('meaning'), data.get('sentence')
    except:
        pass
    
    quotes = ["Success is not final, failure is not fatal: it is the courage to continue that counts.", "The only way to do great work is to love what you do.", "Innovation distinguishes between a leader and a follower.", "Your limitation—it's only your imagination.", "Push yourself, because no one else is going to do it for you."]
    words_data = [("Serendipity", "A pleasant surprise or fortunate accident", "Finding this job was pure serendipity."), ("Resilience", "The ability to recover quickly from difficulties", "Her resilience helped her overcome every challenge."), ("Eloquent", "Fluent and persuasive in speaking or writing", "His eloquent speech moved the entire audience."), ("Perseverance", "Persistence in doing something despite difficulty", "Success requires perseverance and dedication."), ("Innovative", "Featuring new methods; advanced and original", "The company's innovative approach revolutionized the industry.")]
    
    quote, (word, meaning, sentence) = random.choice(quotes), random.choice(words_data)
    try:
        json.dump({'date': today, 'quote': quote, 'word': word, 'meaning': meaning, 'sentence': sentence}, open(DAILY_DATA_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    except:
        pass
    return quote, word, meaning, sentence

def get_outlook_events():
    outlook = win32com.client.Dispatch("Outlook.Application")
    calendar = outlook.GetNamespace("MAPI").GetDefaultFolder(9)
    appointments = calendar.Items
    appointments.Sort("[Start]")
    appointments.IncludeRecurrences = True
    
    today, week_end, events = datetime.now().date(), datetime.now().date() + timedelta(days=2), []
    for item in appointments:
        try:
            item_start = item.Start.date() if hasattr(item.Start, 'date') else None
            if item_start and today <= item_start <= week_end:
                events.append({'subject': item.Subject, 'start': item.Start.strftime('%I:%M %p') if hasattr(item.Start, 'strftime') else str(item.Start), 'end': item.End.strftime('%I:%M %p') if hasattr(item.End, 'strftime') else str(item.End), 'date': item_start.strftime('%a %d'), 'full_date': item_start, 'end_datetime': item.End, 'location': item.Location})
                if len(events) >= 10:
                    break
        except:
            pass
    return events

def toggle_microphone():
    global mike_muted
    mike_muted = not mike_muted
    threading.Thread(target=lambda: _toggle_mic(), daemon=True).start()
    update_mike_button()

def _toggle_mic():
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        volume = cast(AudioUtilities.GetMicrophone().Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None), POINTER(IAudioEndpointVolume))
        volume.SetMute(1 if mike_muted else 0, None)
    except:
        pass

def set_volume(val):
    global volume_timer
    if volume_timer:
        root.after_cancel(volume_timer)
    volume_timer = root.after(50, lambda: threading.Thread(target=lambda: subprocess.Popen(["nircmd", "setsysvolume", str(int(float(val) * 655.35))], shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL), daemon=True).start())

def update_mike_button():
    mike_label.config(image=mic_photo_muted if mike_muted else mic_photo) if mic_photo else mike_label.config(text="🔇" if mike_muted else "🎤")

def blynk_button_click():
    threading.Thread(target=lambda: requests.get("http://blynk.tk:8080/65FhSzpi6hJApqWPwsH-IIrY_8k2BV4K/update/V0?value=4", timeout=5), daemon=True).start()

def blynk_slider_release(event):
    threading.Thread(target=lambda: requests.get(f"http://blynk.tk:8080/65FhSzpi6hJApqWPwsH-IIrY_8k2BV4K/update/V1?value={int(blynk_slider.get())}", timeout=5), daemon=True).start()

def show_paint_screen():
    paint_window = tk.Toplevel(root)
    paint_window.overrideredirect(True)
    paint_window.configure(bg="black")
    paint_window.geometry(f"{width}x{height}+{x}+{y}")
    paint_window.attributes("-topmost", True)
    current_color, show_palette = "white", False
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
            if not os.path.exists("drawings"):
                os.makedirs("drawings")
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join("drawings", f"{timestamp}.png")
            from PIL import Image, ImageDraw
            canvas.update()
            w, h = canvas.winfo_width(), canvas.winfo_height()
            img = Image.new('RGB', (w, h), 'black')
            draw = ImageDraw.Draw(img)
            for item in canvas.find_all():
                coords = canvas.coords(item)
                if canvas.type(item) == 'line' and len(coords) >= 4:
                    for i in range(0, len(coords)-2, 2):
                        x1, y1, x2, y2 = coords[i], coords[i+1], coords[i+2], coords[i+3]
                        color = canvas.itemcget(item, 'fill')
                        width_val = int(float(canvas.itemcget(item, 'width')))
                        for offset in range(-width_val//2, width_val//2 + 1):
                            draw.line([(x1+offset, y1), (x2+offset, y2)], fill=color)
                            draw.line([(x1, y1+offset), (x2, y2+offset)], fill=color)
            img.save(filename, "PNG")
            saved_label = tk.Label(paint_window, text="Saved!", fg="#4CAF50", bg="black", font=("Segoe UI", 16, "bold"))
            saved_label.place(relx=0.5, rely=0.1, anchor="center")
            paint_window.after(2000, saved_label.destroy)
        except:
            pass
    (tk.Button(options_frame, image=new_photo, bg="black", bd=0, relief="flat", command=lambda: canvas.delete("all")) if new_photo else tk.Button(options_frame, text="📄", bg="black", fg="white", font=("Segoe UI", 24), bd=0, relief="flat", command=lambda: canvas.delete("all"))).pack(side="left", padx=15)
    (tk.Button(options_frame, image=save_photo, bg="black", bd=0, relief="flat", command=save_drawing) if save_photo else tk.Button(options_frame, text="💾", bg="black", fg="white", font=("Segoe UI", 24), bd=0, relief="flat", command=save_drawing)).pack(side="left", padx=15)
    (tk.Button(options_frame, image=colors_photo, bg="black", bd=0, relief="flat", command=toggle_palette) if colors_photo else tk.Button(options_frame, text="🎨", bg="black", fg="white", font=("Segoe UI", 24), bd=0, relief="flat", command=toggle_palette)).pack(side="left", padx=15)
    (tk.Button(options_frame, image=back_photo, bg="black", bd=0, relief="flat", command=paint_window.destroy) if back_photo else tk.Button(options_frame, text="◀", bg="black", fg="white", font=("Segoe UI", 24), bd=0, relief="flat", command=paint_window.destroy)).pack(side="left", padx=15)
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

def get_secondary_monitor():
    for attempt in range(30):
        try:
            secondaries = [m for m in get_monitors() if not m.is_primary]
            for m in secondaries:
                if (m.width == 1080 and m.height == 1920) or (m.width == 864 and m.height == 1536):
                    return m
            return None
        except:
            pass
        if attempt < 29:
            import time
            time.sleep(1)
    return None

smaller_monitor = get_secondary_monitor()
if not smaller_monitor:
    print("No monitor with 1080x1920 or 864x1536 resolution found. Exiting.")
    sys.exit(0)

print(f"Using secondary monitor: {smaller_monitor.width}x{smaller_monitor.height}")
x, y, width, height = smaller_monitor.x, smaller_monitor.y, smaller_monitor.width, smaller_monitor.height

root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-transparentcolor", "black")
root.configure(bg="black")
root.geometry(f"{width}x{height}+{x}+{y}")

main_container = tk.Frame(root, bg="black")
main_container.pack(fill="both", expand=True)

def update_calendar():
    def fetch_and_update():
        import pythoncom
        pythoncom.CoInitialize()
        try:
            events = get_outlook_events()
            root.after(0, lambda: display_events(events))
        finally:
            pythoncom.CoUninitialize()
    
    def display_events(events):
        for widget in calendar_list.winfo_children():
            widget.destroy()
        
        now, today = datetime.now(), datetime.now().date()
        if events:
            for event in events[:10]:
                try:
                    event_end = event['end_datetime'].replace(tzinfo=None) if hasattr(event['end_datetime'], 'replace') else event['end_datetime']
                    is_past = event_end < now and event['full_date'] == today
                except:
                    is_past = False
                
                bg_color, fg_time, fg_subject, fg_location = ("#1a1520", "#666666", "#555555", "#444444") if is_past else (CARD_BG, ACCENT_PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY)
                event_frame = ctk.CTkFrame(calendar_list, fg_color=bg_color, border_color=CARD_BORDER, border_width=1, corner_radius=10)
                event_frame.pack(fill="x", pady=3, padx=0, expand=True)
                ctk.CTkLabel(event_frame, text=f"{event['date']} | {event['start']} - {event['end']}", text_color=fg_time, font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=20, pady=(16, 4))
                ctk.CTkLabel(event_frame, text=event['subject'], text_color=fg_subject, font=("Segoe UI", 21), wraplength=676, justify="left").pack(anchor="w", padx=20, pady=(0, 4))
                if event.get('location'):
                    ctk.CTkLabel(event_frame, text=f"📍 {event['location']}", text_color=fg_location, font=("Segoe UI", 17), wraplength=676, justify="left").pack(anchor="w", padx=20, pady=(0, 16))
        else:
            ctk.CTkLabel(calendar_list, text="No meetings in next 2 days", text_color=TEXT_SECONDARY, font=("Segoe UI", 23, "italic")).pack(pady=26)
        
        root.after(600000, update_calendar)
    
    threading.Thread(target=fetch_and_update, daemon=True).start()

top_section = tk.Frame(main_container, bg="black")
top_section.pack(side="top", fill="x", padx=26, pady=(20, 7))

quote, word, meaning, sentence = get_daily_inspiration()

thought_card = create_card_frame(top_section, "💭 Thought of the Day")
thought_card.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=5)
ctk.CTkLabel(thought_card, text=f'"{quote}"', text_color=TEXT_PRIMARY, font=("Segoe UI", 23, "italic"), wraplength=520, justify="center").pack(pady=(13, 20), padx=26)

word_card = create_card_frame(top_section, "📚 Word of the Day")
word_card.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=5)
ctk.CTkLabel(word_card, text=f"💡 {word}", text_color=ACCENT_PRIMARY, font=("Segoe UI", 26, "bold")).pack(pady=(13, 7))
ctk.CTkLabel(word_card, text=meaning, text_color=TEXT_SECONDARY, font=("Segoe UI", 21, "bold"), wraplength=455, justify="center").pack(pady=(0, 7))
ctk.CTkLabel(word_card, text=f'"{sentence}"', text_color=TEXT_SECONDARY, font=("Segoe UI", 18, "italic"), wraplength=455, justify="center").pack(pady=(0, 20))

clock_section = tk.Frame(main_container, bg="black")
clock_section.pack(side="top", pady=5)

clock_labels = {}
for zone in CITIES:
    zone_card = create_card_frame(clock_section)
    zone_card.pack(side="left", padx=8)
    ctk.CTkLabel(zone_card, text=zone, text_color=TEXT_SECONDARY, font=("Segoe UI", 21)).pack(padx=26, pady=(13, 7))
    time_label = ctk.CTkLabel(zone_card, text="", text_color=ACCENT_PRIMARY, font=("Segoe UI", 42, "bold"))
    time_label.pack(padx=26, pady=(0, 13))
    clock_labels[zone] = time_label

mike_muted, volume_timer = False, None

try:
    paint_photo = ImageTk.PhotoImage(Image.open("icons/paint.png").resize((64, 64), Image.Resampling.LANCZOS))
    mic_icon = Image.open("icons/mic.png").resize((64, 64), Image.Resampling.LANCZOS)
    mic_photo = ImageTk.PhotoImage(mic_icon)
    mic_icon_muted = mic_icon.copy()
    mic_icon_muted.putalpha(128)
    mic_photo_muted = ImageTk.PhotoImage(mic_icon_muted)
    volume_photo = ImageTk.PhotoImage(Image.open("icons/volume.png").resize((64, 64), Image.Resampling.LANCZOS))
    brightness_photo = ImageTk.PhotoImage(Image.open("icons/brightness.png").resize((64, 64), Image.Resampling.LANCZOS))
    power_photo = ImageTk.PhotoImage(Image.open("icons/power.png").resize((64, 64), Image.Resampling.LANCZOS))
    new_photo = ImageTk.PhotoImage(Image.open("icons/new.png").resize((96, 96), Image.Resampling.LANCZOS))
    back_photo = ImageTk.PhotoImage(Image.open("icons/back.png").resize((96, 96), Image.Resampling.LANCZOS))
    save_photo = ImageTk.PhotoImage(Image.open("icons/save.png").resize((96, 96), Image.Resampling.LANCZOS))
    colors_photo = ImageTk.PhotoImage(Image.open("icons/colors.png").resize((96, 96), Image.Resampling.LANCZOS))
    clock_photo = ImageTk.PhotoImage(Image.open("icons/clock.png").resize((48, 48), Image.Resampling.LANCZOS))
    weather_photo = ImageTk.PhotoImage(Image.open("icons/weather.png").resize((48, 48), Image.Resampling.LANCZOS))
    charging_photo = ImageTk.PhotoImage(Image.open("icons/charging.png").resize((48, 48), Image.Resampling.LANCZOS))
    onbattery_photo = ImageTk.PhotoImage(Image.open("icons/onbattery.png").resize((48, 48), Image.Resampling.LANCZOS))
except:
    paint_photo = mic_photo = mic_photo_muted = volume_photo = brightness_photo = power_photo = new_photo = back_photo = save_photo = colors_photo = clock_photo = charging_photo = onbattery_photo = weather_photo = None

info_section = tk.Frame(main_container, bg="black")
info_section.pack(side="top", pady=5)

battery_card = create_card_frame(info_section)
battery_card.pack(side="left", padx=8)
battery_icon_label = tk.Label(battery_card, bg=CARD_BG)
battery_icon_label.pack(side="left", padx=(10, 5), pady=8)
battery_label = tk.Label(battery_card, text="--", fg=TEXT_PRIMARY, bg=CARD_BG, font=("Segoe UI", 18, "bold"))
battery_label.pack(side="left", padx=(0, 13), pady=10)

weather_card = create_card_frame(info_section)
weather_card.pack(side="left", padx=8)
weather_icon_label = tk.Label(weather_card, bg=CARD_BG)
weather_icon_label.pack(side="left", padx=(10, 5), pady=8)
weather_label = tk.Label(weather_card, text="--", fg=TEXT_PRIMARY, bg=CARD_BG, font=("Segoe UI", 18, "bold"), wraplength=156)
weather_label.pack(side="left", padx=(0, 13), pady=10)

attendance_card = create_card_frame(info_section)
attendance_card.pack(side="left", padx=8)
attendance_icon_label = tk.Label(attendance_card, bg=CARD_BG)
attendance_icon_label.pack(side="left", padx=(10, 5), pady=8)
attendance_label = tk.Label(attendance_card, text="--", fg=TEXT_PRIMARY, bg=CARD_BG, font=("Segoe UI", 18, "bold"))
attendance_label.pack(side="left", padx=(0, 13), pady=10)

bottom_section = tk.Frame(main_container, bg="black")
bottom_section.pack(side="top", fill="both", expand=True, padx=26, pady=13)
bottom_section.grid_columnconfigure(0, weight=1, uniform="equal")
bottom_section.grid_columnconfigure(1, weight=1, uniform="equal")
bottom_section.grid_rowconfigure(0, weight=1)

notes_card = create_card_frame(bottom_section, "📝 My Notes")
notes_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
notes_text = tk.Text(notes_card, font=("Segoe UI", 21), wrap="word", bg="#252535", fg=TEXT_PRIMARY, bd=0, padx=26, pady=20, insertbackground=ACCENT_PRIMARY, relief="flat")
notes_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
notes_text.bind('<KeyRelease>', lambda e: save_notes())

calendar_card = create_card_frame(bottom_section, "📅 Upcoming Meetings")
calendar_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
calendar_scroll_frame = tk.Frame(calendar_card, bg=CARD_BG)
calendar_scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
calendar_canvas = tk.Canvas(calendar_scroll_frame, bg=CARD_BG, highlightthickness=0)
calendar_list = tk.Frame(calendar_canvas, bg=CARD_BG)
calendar_canvas.create_window((0, 0), window=calendar_list, anchor="nw")
calendar_canvas.pack(fill="both", expand=True)

scroll_start_y, last_scroll_y = 0, 0

def on_mouse_wheel(event):
    calendar_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

def start_scroll(event):
    global scroll_start_y, last_scroll_y
    scroll_start_y = last_scroll_y = event.y_root

def do_scroll(event):
    global last_scroll_y
    calendar_canvas.yview_scroll(int((last_scroll_y - event.y_root)/10), "units")
    last_scroll_y = event.y_root

calendar_list.bind("<Configure>", lambda e: calendar_canvas.configure(scrollregion=calendar_canvas.bbox("all")))
for widget in [calendar_canvas, calendar_list]:
    widget.bind("<Enter>", lambda e: calendar_canvas.bind_all("<MouseWheel>", on_mouse_wheel))
    widget.bind("<Leave>", lambda e: calendar_canvas.unbind_all("<MouseWheel>"))
    widget.bind("<Button-1>", start_scroll)
    widget.bind("<B1-Motion>", do_scroll)
    widget.bind("<ButtonRelease-1>", lambda e: None)

footer = ctk.CTkFrame(root, fg_color=CARD_BG, border_color=CARD_BORDER, border_width=2, corner_radius=15, height=130)
footer.pack(side="bottom", fill="x", padx=26, pady=26)

paint_button = tk.Label(footer, image=paint_photo, bg=CARD_BG, cursor="hand2", bd=0) if paint_photo else tk.Label(footer, text="🎨", fg=TEXT_PRIMARY, bg=CARD_BG, font=("Segoe UI", 32), cursor="hand2", bd=0)
paint_button.pack(side="left", padx=20, pady=20)
paint_button.bind("<Button-1>", lambda e: show_paint_screen())

controls_container = tk.Frame(footer, bg=CARD_BG)
controls_container.pack(side="right", padx=20, pady=15)

brightness_frame = tk.Frame(controls_container, bg=CARD_BG)
brightness_frame.pack(side="left", padx=(0, 20))
(tk.Label(brightness_frame, image=brightness_photo, bg=CARD_BG) if brightness_photo else tk.Label(brightness_frame, text="☀️", fg=TEXT_PRIMARY, bg=CARD_BG, font=("Segoe UI", 24))).pack(pady=(0, 5))
blynk_slider = tk.Scale(brightness_frame, from_=255, to=0, orient="vertical", bg=CARD_BG, fg=ACCENT_PRIMARY, troughcolor="#2d2d44", activebackground=ACCENT_PRIMARY, highlightthickness=0, length=120, width=30, sliderlength=20, bd=0, showvalue=False)
blynk_slider.bind("<ButtonRelease-1>", blynk_slider_release)
blynk_slider.pack()
if power_photo:
    blynk_button = tk.Label(brightness_frame, image=power_photo, bg=CARD_BG, cursor="hand2", bd=0)
    blynk_button.pack(pady=(5, 0))
    blynk_button.bind("<Button-1>", lambda e: blynk_button_click())
else:
    tk.Button(brightness_frame, text="⏻", bg=ACCENT_PRIMARY, fg="#000000", font=("Segoe UI", 16, "bold"), command=blynk_button_click, bd=0, padx=10, pady=5, relief="flat", cursor="hand2").pack(pady=(5, 0))

volume_frame = tk.Frame(controls_container, bg=CARD_BG)
volume_frame.pack(side="left")
(tk.Label(volume_frame, image=volume_photo, bg=CARD_BG) if volume_photo else tk.Label(volume_frame, text="🔊", fg=TEXT_PRIMARY, bg=CARD_BG, font=("Segoe UI", 24))).pack(pady=(0, 5))
vol_slider = tk.Scale(volume_frame, from_=100, to=0, orient="vertical", bg=CARD_BG, fg=ACCENT_PRIMARY, troughcolor="#2d2d44", activebackground=ACCENT_PRIMARY, highlightthickness=0, command=set_volume, length=120, width=30, sliderlength=20, bd=0, showvalue=False)
vol_slider.set(50)
vol_slider.pack()
mike_label = tk.Label(volume_frame, image=mic_photo, bg=CARD_BG, cursor="hand2", bd=0) if mic_photo else tk.Label(volume_frame, text="🎤", fg=TEXT_PRIMARY, bg=CARD_BG, font=("Segoe UI", 20), cursor="hand2", bd=0)
mike_label.pack(pady=(5, 0))
mike_label.bind("<Button-1>", lambda e: toggle_microphone())
update_mike_button()

attendance_done = False
tz_cache = {zone: pytz.timezone(tz) for zone, (_, tz) in CITIES.items()}

def update_time():
    for zone in CITIES:
        clock_labels[zone].configure(text=datetime.now(tz_cache[zone]).strftime('%I:%M:%S %p'))
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
        root.after(0, lambda: attendance_label.config(text=value))
        if value != "--":
            attendance_done = True
        else:
            root.after(ATTENDANCE_RETRY_MS, update_attendance)
    if not attendance_done:
        threading.Thread(target=task, daemon=True).start()

notes_text.insert("1.0", load_notes())
update_time()
update_right()
update_attendance()
update_calendar()

root.protocol("WM_DELETE_WINDOW", lambda: (save_notes(), root.destroy()))
root.mainloop()
