# gui.py
# Graphical User Interface for Weather Monitoring System
# SF4: Data Logger
# jz587 and ak2444

#Import Necessary Modules
import tkinter as tk
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
#import statistics
import arduino_communication

MAX_POINTS = 50 

# Start the serial reader first
arduino_communication.start_reader()

# Build the Tkinter Root
root = tk.Tk()
root.title("Weather Monitoring System")
root.geometry("1200x800")
root.configure(bg="#1e1e2e")

# Live values
display_temp = tk.StringVar(value="-- °C")
display_humidity = tk.StringVar(value="-- %")
display_pressure = tk.StringVar(value="-- hPa")
display_lux = tk.StringVar(value="-- lux")
display_windspeed = tk.StringVar(value="--")

# Summary values 
summary_temp = tk.StringVar(value="-- °C")
summary_hum = tk.StringVar(value="-- %")
summary_lux = tk.StringVar(value="-- lux")
summary_wind = tk.StringVar(value="--")

# Colour Gradient Parameters
gradient_dict = {
    "TEMP": {"lo": 10.0, "hi": 30.0, "c_lo": (0, 150, 200), "c_hi": (255, 85, 0)},
    "HUM": {"lo": 0.0, "hi": 100.0, "c_lo": (200, 200, 200), "c_hi": (65, 105, 225)},
    "LUX": {"lo": 0.0, "hi": 1000.0, "c_lo": (120, 120, 120), "c_hi": (255, 240, 200)},
}

# Function for determing colour of label depending on sensor value
def assign_colours(sensor, reading):
        if sensor in gradient_dict:
            lo = gradient_dict[sensor]["lo"]
            hi = gradient_dict[sensor]["hi"]
            c_lo = gradient_dict[sensor]["c_lo"]
            c_hi =  gradient_dict[sensor]["c_hi"]
            fraction = (reading - lo) / (hi - lo)
            r = int(c_lo[0] + (c_hi[0] - c_lo[0]) * fraction)
            g = int(c_lo[1] + (c_hi[1] - c_lo[1]) * fraction)
            b = int(c_lo[2] + (c_hi[2] - c_lo[2]) * fraction)
            return f"#{r:02x}{g:02x}{b:02x}"
        else:
            return "#f5f5f5"

# Calculate Moving Average to obtain a smoother curve
def moving_avg(buffer, samples):
    moving_avgs = []
    global masamples
    masamples = int(samples)
    for i in range(len(buffer)):
        if i < (masamples - 1):
            moving_avgs.append(buffer[i])
        else:
            window = buffer[i-(masamples-1): i+1]
            temp = sum(window) / masamples
            moving_avgs.append(temp)
    return moving_avgs

# GUI Frames
frames = {}

def show_frame(name):
    for f in frames.values():
        f.pack_forget()
    frames[name].pack(fill="both", expand=True)

# Updating live values
def update_live_values():
    if len(arduino_communication.temperatures) > 0:
        new_temp = arduino_communication.temperatures[-1]
        display_temp.set(f"🌡️ {new_temp:.2f} °C")
        temp_label.config(fg=assign_colours("TEMP", new_temp))
        # Update summary without icon
        summary_temp.set(f"{new_temp:.0f} °C")

    if len(arduino_communication.humidities) > 0:
        new_hum = arduino_communication.humidities[-1]
        display_humidity.set(f"💧 {new_hum:.2f} %")
        hum_label.config(fg=assign_colours("HUM", new_hum))
        summary_hum.set(f"{new_hum:.0f} %")

    if len(arduino_communication.luxintensities) > 0:
        new_lux = arduino_communication.luxintensities[-1]
        display_lux.set(f"💡 {new_lux:.2f} lux")
        lux_label.config(fg=assign_colours("LUX", new_lux))
        summary_lux.set(f"{new_lux:.0f} lux")

    if len(arduino_communication.pressures) > 0:
        new_pressure = arduino_communication.pressures[-1]
        display_pressure.set(f"🌪️ {new_pressure:.2f} hPa")
        pressure_label.config(fg=assign_colours("PRES", new_pressure))

    if len(arduino_communication.wind_speeds) > 0:
        temp_windspeed = arduino_communication.wind_speeds[-1]
        if temp_windspeed < 0.20:
            new_windspeed = 0
            wind_desc = "No Wind"
        elif temp_windspeed > 3.5:
            new_windspeed = 36
            wind_desc = "Strong Wind"
        else:
            new_windspeed = (temp_windspeed - 0.20) / 0.5
            wind_desc = "Mild Wind"

        display_windspeed.set(f"🌬️ {wind_desc}")
        windspeed_label.config(fg=assign_colours("WS", new_windspeed))
        summary_wind.set(f"{wind_desc}")

    root.after(1000, update_live_values)


# Update home live plots
def update_live_plots(_):
    td = arduino_communication.temperatures[-MAX_POINTS:]
    hd = arduino_communication.humidities[-MAX_POINTS:]
    ld = arduino_communication.luxintensities[-MAX_POINTS:]

    tma = moving_avg(td, 5)
    hma = moving_avg(hd, 5)
    lma = moving_avg(ld, 5)

    buffers = {
    "TEMP": {"data": td, "madata": tma, "Variable": "Temperature", "Unit": "°C", "AXIS" : axes[0], "THRESH" : 26},
    "HUM": {"data": hd, "madata": hma, "Variable": "Humidity", "Unit": "%", "AXIS" : axes[1], "THRESH" : 60},
    "LUX": {"data": ld, "madata": lma, "Variable": "Light Intensity", "Unit": "lux", "AXIS" : axes[2], "THRESH" : 100}
    }

    # for buf, ma_buf, title, unit, ax, thresh in buffers:
    #buffers = [(td, tma, "Temperature", "°C", axes[0], 26), (hd, hma, "Humidity", "%", axes[1], 60), (ld, lma, "Light", "lux", axes[2], 50)]
    for key, value in buffers.items():
        buf      = value["data"]
        ma_buf   = value["madata"]
        title    = value["Variable"]
        unit     = value["Unit"]
        ax       = value["AXIS"]
        thresh   = value["THRESH"]

        ax.clear()        
        if ma_buf and len(ma_buf) == len(buf):
            ax.plot(
                ma_buf,
                color="#ffe082",
                linestyle="--",
                linewidth=1.2,
                label=f"{masamples}-sample Moving Average"
            )
        ax.plot(buf, color="#80cbc4", linewidth=1.2, label="Raw")


        ax.axhline(y=thresh, color="#ff8a65", linewidth=1)

        if title == "Temperature":
            xs = [i for i, v in enumerate(buf) if v > thresh]
            ys = [buf[i] for i in xs]
            ax.scatter(xs, ys, color="#e57373", s=30, label=">26°C")
        elif title == "Humidity":
            xs = [i for i, v in enumerate(buf) if v > thresh]
            ys = [buf[i] for i in xs]
            ax.scatter(xs, ys, color="#64b5f6", s=30, label=">60%")
        elif title == "Light":
            xs = [i for i, v in enumerate(buf) if v < thresh]
            ys = [buf[i] for i in xs]
            ax.scatter(xs, ys, color="#ffb74d", s=30, label="<50 lux")

        ax.set_title(
            title,
            color="white",
            pad=6,
            fontdict={"family": "Verdana", "size": 24, "weight": "bold"}
        )
        ax.set_ylabel(
            unit,
            color="white",
            fontdict={"family": "Verdana", "size": 20}
        )
        ax.set_facecolor("#1e1e2e")
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.tick_params(axis='x', colors='white', labelrotation=45)
        ax.tick_params(axis='y', colors='white')
        ax.title.set_color("white")
        ax.yaxis.label.set_color("white")
        ax.set_ylim(bottom=0)
        ax.legend(
            loc="upper right",
            facecolor="#2e2e3e",
            edgecolor="#555555",
            labelcolor="white",
            fontsize = 20
        )


historical_canvases = {}


def compute_stats(data):
    if len(data) == 0:
        return (None, None, None)
    minimum = min(data)
    maximum = max(data)
    avg = sum(data) / len(data)
    return (minimum, maximum, avg)

# Update plots of old data
def update_historical_plot(sensor_key):
    if sensor_key == "TEMP":
        buf = arduino_communication.temperatures
    elif sensor_key == "HUM":
        buf = arduino_communication.humidities
    elif sensor_key == "PRES":
        buf = arduino_communication.pressures
    elif sensor_key == "LUX":
        buf = arduino_communication.luxintensities
    elif sensor_key == "WIND":
        buf = arduino_communication.wind_speeds
    else:
        buf = []

    mn, mx, avg = compute_stats(buf)

    min_lbl, max_lbl, avg_lbl, fig_hist, ax_hist, ax_hist100, ax_hist200, canvas_hist = historical_canvases[sensor_key]

    if mn is None:
        min_lbl.config(text="Min: —")
        max_lbl.config(text="Max: —")
        avg_lbl.config(text="Avg: —")
    else:
        min_lbl.config(text=f"Min: {mn:.2f}")
        max_lbl.config(text=f"Max: {mx:.2f}")
        avg_lbl.config(text=f"Avg: {avg:.2f}")

    ax_hist.clear()
    ax_hist.plot(buf, color="#80cbc4", linewidth=1.5)
    quick_dict2 = {
        "TEMP": "Temperature",
        "HUM":  "Humidity",
        "PRES": "Pressure",
        "WIND": "Wind Speed",
        "LUX":  "Light Intensity"
    }
    ax_hist.set_title(
        f"{quick_dict2[sensor_key]} : All samples",
        color="white",
        fontdict={ "family": "Verdana", "size": 18, "weight": "bold" }
    )
    ax_hist.set_facecolor("#1e1e2e")
    ax_hist.grid(True, linestyle="--", alpha=0.3)
    ax_hist.tick_params(axis='x', colors='white', labelrotation=45)
    ax_hist.tick_params(axis='y', colors='white')
    ax_hist.set_ylabel(
        sensor_key,
        color="white",
        fontdict={ "family": "Verdana", "size": 16 }
    )

    ax_hist100.clear()
    lenbuf = len(buf)
    ax_hist100.plot(buf[(lenbuf - 101) : (lenbuf - 1)], color="#80cbc4", linewidth=1.5)
    quick_dict2 = {
        "TEMP": "Temperature",
        "HUM":  "Humidity",
        "PRES": "Pressure",
        "WIND": "Wind Speed",
        "LUX":  "Light Intensity"
    }
    ax_hist100.set_title(
        f"{quick_dict2[sensor_key]} : Last 100 Samples",
        color="white",
        fontdict={ "family": "Verdana", "size": 18, "weight": "bold" }
    )
    ax_hist100.set_facecolor("#1e1e2e")
    ax_hist100.grid(True, linestyle="--", alpha=0.3)
    ax_hist100.tick_params(axis='x', colors='white', labelrotation=45)
    ax_hist100.tick_params(axis='y', colors='white')
    ax_hist100.set_ylabel(
        sensor_key,
        color="white",
        fontdict={ "family": "Verdana", "size": 16 }
    )

    ax_hist200.clear()
    lenbuf2 = len(buf)
    ax_hist200.plot(buf[(lenbuf2 - 201) : (lenbuf2 - 1)], color="#80cbc4", linewidth=1.5)
    quick_dict2 = {
        "TEMP": "Temperature",
        "HUM":  "Humidity",
        "PRES": "Pressure",
        "WIND": "Wind Speed",
        "LUX":  "Light Intensity"
    }
    ax_hist200.set_title(
        f"{quick_dict2[sensor_key]} : Last 200 samples",
        color="white",
        fontdict={ "family": "Verdana", "size": 18, "weight": "bold" }
    )
    ax_hist200.set_facecolor("#1e1e2e")
    ax_hist200.grid(True, linestyle="--", alpha=0.3)
    ax_hist200.tick_params(axis='x', colors='white', labelrotation=45)
    ax_hist200.tick_params(axis='y', colors='white')
    ax_hist200.set_ylabel(
        sensor_key,
        color="white",
        fontdict={ "family": "Verdana", "size": 16 }
    )

    fig_hist.tight_layout(pad=0, h_pad=0) 
    canvas_hist.draw()

# Creating individual sensor pages
def create_sensor_page(sensor_key):
    frame = tk.Frame(root, bg="#1e1e2e")
    frames[sensor_key] = frame

    top = tk.Frame(frame, bg="#2e2e3e", bd=1, relief="raised")
    top.pack(fill="x")
    tk.Button(
        top,
        text="Back",
        font=("Verdana", 20),
        bg="#2e2e2e", fg="white",
        activebackground="#3a3a3a", activeforeground="white",
        bd=0,
        command=lambda: show_frame("home")
    ).pack(side="left", padx=15, pady=10)
    quick_dict = {
        "TEMP": "Temperature",
        "HUM":  "Humidity",
        "PRES": "Pressure",
        "WIND": "Wind Speed",
        "LUX":  "Light Intensity"
    }
    tk.Label(
        top,
        text=f"{quick_dict[sensor_key]} Details",
        font=("Verdana", 22, "bold"),
        fg="white",
        bg="#2e2e3e"
    ).pack(side="left", padx=10)

    live_frame = tk.Frame(frame, bg="#1e1e2e")
    live_frame.pack(pady=30)
    big = tk.Label(
        live_frame,
        textvariable={
            "TEMP": display_temp,
            "HUM":  display_humidity,
            "PRES": display_pressure,
            "LUX":  display_lux,
            "WIND": display_windspeed
        }[sensor_key],
        font=("Verdana", 48),
        fg="#00ff99",
        bg="#1e1e2e"
    )
    big.pack()

    def recolour_big(*args):
        try:
            val = float(big.cget("text").split()[1])
        except:
            return
        big.config(fg=assign_colours(sensor_key, val))

    {
        "TEMP": display_temp,
        "HUM":  display_humidity,
        "PRES": display_pressure,
        "LUX":  display_lux,
        "WIND": display_windspeed
    }[sensor_key].trace_add("write", recolour_big)

    stats_f = tk.Frame(frame, bg="#1e1e2e", bd=1, relief="solid", padx=20, pady=15)
    stats_f.pack(pady=20, padx=50)

    stats_inner = tk.Frame(stats_f, bg="#1e1e2e")
    stats_inner.pack()

    min_lbl = tk.Label(
        stats_inner,
        text="Min: —",
        font=("Verdana", 36, "bold"),
        fg="white",
        bg="#1e1e2e"
    )
    max_lbl = tk.Label(
        stats_inner,
        text="Max: —",
        font=("Verdana", 36, "bold"),
        fg="white",
        bg="#1e1e2e"
    )
    avg_lbl = tk.Label(
        stats_inner,
        text="Avg: —",
        font=("Verdana", 36, "bold"),
        fg="white",
        bg="#1e1e2e"
    )

    min_lbl.pack(side="left", padx=40)
    max_lbl.pack(side="left", padx=40)
    avg_lbl.pack(side="left", padx=40)

    hist_frame = tk.Frame(frame, bg="#1e1e2e")
    hist_frame.pack(expand=True, fill="both", padx=50, pady=10)

    fig_hist = plt.Figure(figsize=(12, 6), dpi=200, facecolor="#1e1e2e")
    ax_hist = fig_hist.add_subplot(311)
    ax_hist.set_facecolor("#1e1e2e")
    ax_hist100 = fig_hist.add_subplot(312)
    ax_hist100.set_facecolor("#1e1e2e")
    ax_hist200 = fig_hist.add_subplot(313)
    ax_hist200.set_facecolor("#1e1e2e")

    canvas_hist = FigureCanvasTkAgg(fig_hist, master=hist_frame)
    canvas_hist.get_tk_widget().pack(expand=True, fill="both", anchor="center")

    historical_canvases[sensor_key] = (min_lbl, max_lbl, avg_lbl, fig_hist, ax_hist, ax_hist100, ax_hist200, canvas_hist)

    update_historical_plot(sensor_key)

    return frame

for key in ["TEMP", "HUM", "PRES", "LUX", "WIND"]:
    create_sensor_page(key)

old_frame = show_frame

def show_frame(name):
    if name in ["TEMP", "HUM", "PRES", "LUX", "WIND"]:
        update_historical_plot(name)
    old_frame(name)

# Home page
home = tk.Frame(root, bg="#1e1e2e")
frames["home"] = home

tk.Label(
    home,
    text="🌦️ Weather Monitoring System",
    font=("Verdana", 72, "bold"),
    fg="white", bg="#1e1e2e"
).pack(pady=20)

# Weather Summary Section
summary_frame = tk.Frame(home, bg="#1e1e2e")
summary_frame.pack(fill="x", pady=10)

summary_center = tk.Frame(summary_frame, bg="#1e1e2e")
summary_center.pack(pady=0)

summary_left = tk.Frame(summary_center, bg="#1e1e2e")
summary_left.pack(side="left", padx=20)

tk.Label(
    summary_left,
    textvariable=summary_temp,
    font=("Verdana", 56, "bold"),
    fg="white",
    bg="#1e1e2e"
).pack()

summary_right = tk.Frame(summary_center, bg="#1e1e2e")
summary_right.pack(side="left", padx=50)

tk.Label(
    summary_right,
    textvariable=summary_hum,
    font=("Verdana", 24),
    fg="#dcdcdc",
    bg="#1e1e2e"
).pack(anchor="w", pady=2)

tk.Label(
    summary_right,
    textvariable=summary_lux,
    font=("Verdana", 24),
    fg="#dcdcdc",
    bg="#1e1e2e"
).pack(anchor="w", pady=2)

tk.Label(
    summary_right,
    textvariable=summary_wind,
    font=("Verdana", 24),
    fg="#dcdcdc",
    bg="#1e1e2e"
).pack(anchor="w", pady=2)

# Live value displays
panels = tk.Frame(home, bg="#1e1e2e")
panels.pack(fill="x", pady=10)

def live_dashboard(parent, label_text, var):
    frm = tk.Frame(parent, bg="#1e1e2e", padx=15, pady=10)
    frm.config(highlightbackground="#2e2e2e", highlightthickness=1)
    lbl1 = tk.Label(frm, text=label_text, font=("Verdana", 32), fg="#dcdcdc", bg="#1e1e2e")
    lbl2 = tk.Label(frm, textvariable=var, font=("Verdana", 32), fg="#ffffff", bg="#1e1e2e")
    lbl1.pack()
    lbl2.pack()
    return frm, lbl2

temp_card, temp_label = live_dashboard(panels, "Temperature", display_temp)
hum_card, hum_label = live_dashboard(panels, "Humidity", display_humidity)
lux_card, lux_label = live_dashboard(panels, "Light", display_lux)
pressure_card, pressure_label = live_dashboard(panels, "Barometric Pressure", display_pressure)
windspeed_card, windspeed_label = live_dashboard(panels, "Wind Speed", display_windspeed)

for c in (temp_card, hum_card, lux_card, pressure_card, windspeed_card):
    c.pack(side="left", expand=True, fill="both", padx=30, pady=5)

# Home Page buttons
tk.Button(
    temp_card,
    text="Details",
    font=("Verdana", 22),
    bg="#2e2e2e", fg="white",
    activebackground="#3a3a3a", activeforeground="white",
    bd=0,
    command=lambda: show_frame("TEMP")
).pack(pady=(5,0))

tk.Button(
    hum_card,
    text="Details",
    font=("Verdana", 22),
    bg="#2e2e2e", fg="white",
    activebackground="#3a3a3a", activeforeground="white",
    bd=0,
    command=lambda: show_frame("HUM")
).pack(pady=(5,0))

tk.Button(
    lux_card,
    text="Details",
    font=("Verdana", 22),
    bg="#2e2e2e", fg="white",
    activebackground="#3a3a3a", activeforeground="white",
    bd=0,
    command=lambda: show_frame("LUX")
).pack(pady=(5,0))

tk.Button(
    pressure_card,
    text="Details",
    font=("Verdana", 22),
    bg="#2e2e2e", fg="white",
    activebackground="#3a3a3a", activeforeground="white",
    bd=0,
    command=lambda: show_frame("PRES")
).pack(pady=(5,0))

tk.Button(
    windspeed_card,
    text="Details",
    font=("Verdana", 22),
    bg="#2e2e2e", fg="white",
    activebackground="#3a3a3a", activeforeground="white",
    bd=0,
    command=lambda: show_frame("WIND")
).pack(pady=(5,0))

plot_container = tk.Frame(home, bg="#1e1e2e")
plot_container.pack(expand=True, fill="both", padx=10, pady=10)

fig, axes = plt.subplots(1, 3, figsize=(12, 5), dpi=100)
fig.patch.set_facecolor("#1e1e2e")
for ax in axes:
    ax.set_facecolor("#1e1e2e")

canvas = FigureCanvasTkAgg(fig, master=plot_container)
canvas.get_tk_widget().pack(expand=True, fill="both")

ani = animation.FuncAnimation(fig, update_live_plots, interval=500)

show_frame("home")
root.after(1000, update_live_values)
root.mainloop()
