import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

LAT = 40.5825
LON = 22.9533

st.set_page_config(page_title="Weather Tomorrow", layout="centered")


# -------------------
# 🧊 SNAPSHOT SYSTEM
# -------------------
@st.cache_data(ttl=3600)
def get_weather_snapshot():

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": LAT,
        "longitude": LON,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max",
        "hourly": "temperature_2m,relative_humidity_2m,cloud_cover,wind_speed_10m,precipitation_probability",
        "timezone": "Europe/Athens"
    }

    r = requests.get(url, timeout=10, params=params)
    data = r.json()

    daily = data["daily"]
    hourly = data["hourly"]

    tomorrow = (datetime.now() + timedelta(days=1)).date()

    times = []
    temps = []
    rain_probs = []

    for i, t in enumerate(hourly["time"]):
        if str(t).startswith(str(tomorrow)):
            times.append(t[11:16])
            temps.append(hourly["temperature_2m"][i])
            rain_probs.append(hourly["precipitation_probability"][i])

    if len(temps) == 0:
        return None

    return {
        "max": daily["temperature_2m_max"][1],
        "min": daily["temperature_2m_min"][1],
        "rain_max": daily["precipitation_probability_max"][1],
        "wind": daily["wind_speed_10m_max"][1],

        "times": times,
        "temps": temps,
        "rain_probs": rain_probs,

        "avg_temp": sum(temps) / len(temps),
        "updated": datetime.now().strftime("%H:%M:%S")
    }


# -------------------
# 🌧️ RAIN BLOCK DETECTOR (UMBRELLA LOGIC)
# -------------------
def detect_rain_blocks(times, rain_probs, threshold=40):

    blocks = []
    start = None

    for i in range(len(times)):
        if rain_probs[i] >= threshold:
            if start is None:
                start = i
        else:
            if start is not None:
                blocks.append((start, i - 1))
                start = None

    if start is not None:
        blocks.append((start, len(times) - 1))

    return blocks


# -------------------
# LOAD DATA
# -------------------
om = get_weather_snapshot()

if om is None:
    st.error("No weather data available")
    st.stop()


df = pd.DataFrame({
    "Hour": om["times"],
    "Temp": om["temps"]
})


# -------------------
# STYLE
# -------------------
st.markdown("""
<style>

.big {
    font-size: 70px;
    font-weight: 300;
    text-align: center;
}

.sub {
    text-align: center;
    opacity: 0.6;
    margin-bottom: 10px;
}

.card {
    background: rgba(240,240,240,0.7);
    padding: 14px;
    border-radius: 16px;
    margin-bottom: 10px;
}

.row {
    display: flex;
    justify-content: space-between;
    padding: 10px;
    border-radius: 10px;
    margin-bottom: 6px;
}

.hot { background: rgba(255, 99, 71, 0.25); }
.warm { background: rgba(255, 165, 0, 0.25); }
.cool { background: rgba(135, 206, 250, 0.25); }
.cold { background: rgba(70, 130, 180, 0.25); }

.rain {
    background: rgba(30, 144, 255, 0.25);
}

</style>
""", unsafe_allow_html=True)


# -------------------
# HEADER
# -------------------
st.title("🌦️ Kalamaria Weather (Tomorrow Snapshot)")

st.markdown(f"""
<div class="big">{om['avg_temp']:.0f}°</div>
<div class="sub">Stable forecast • updated {om['updated']}</div>
""", unsafe_allow_html=True)


# -------------------
# CARDS
# -------------------
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div class="card">
    🌡️ Max: <b>{om['max']:.1f}°C</b>
    </div>

    <div class="card">
    🌧️ Rain chance: <b>{om['rain_max']}%</b>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="card">
    🌡️ Min: <b>{om['min']:.1f}°C</b>
    </div>

    <div class="card">
    💨 Wind: <b>{om['wind']:.1f} km/h</b>
    </div>
    """, unsafe_allow_html=True)


# -------------------
# 📊 GRAPH
# -------------------
st.subheader("📊 Hourly Temperature")

st.line_chart(df.set_index("Hour"))


# -------------------
# ☂️ UMBRELLA SYSTEM (MAIN FEATURE)
# -------------------
st.subheader("☂️ Umbrella Recommendation")

blocks = detect_rain_blocks(om["times"], om["rain_probs"])

if not blocks:
    st.success("No umbrella needed tomorrow 🌤️")
else:
    for b in blocks:

        start_time = om["times"][b[0]]
        end_time = om["times"][b[1]]

        max_rain = max(om["rain_probs"][b[0]:b[1] + 1])

        st.markdown(f"""
        <div class="row rain">
            <div>☂️ {start_time} → {end_time}</div>
            <div>{max_rain}% max rain</div>
        </div>
        """, unsafe_allow_html=True)

    st.warning("Bring an umbrella during these periods ☂️")


# -------------------
# 🌈 HOURLY BREAKDOWN (COLOR CODED)
# -------------------
st.subheader("🕐 Hourly Breakdown")

for i in range(len(om["temps"])):

    temp = om["temps"][i]
    time = om["times"][i]

    if temp >= 30:
        cls = "row hot"
    elif temp >= 24:
        cls = "row warm"
    elif temp >= 16:
        cls = "row cool"
    else:
        cls = "row cold"

    st.markdown(f"""
    <div class="{cls}">
        <div>{time}</div>
        <div>{temp:.1f}°C</div>
    </div>
    """, unsafe_allow_html=True)