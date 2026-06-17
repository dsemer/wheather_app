import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

    # -------------------
    # APP CONFIG
    # -------------------
    st.set_page_config(
        page_title="Kalamaria Weather",
        page_icon="🌦️",
        layout="centered"
    )

    LAT = 40.5825
    LON = 22.9533

    # -------------------
    # WEATHER SNAPSHOT
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

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        daily = data["daily"]
        hourly = data["hourly"]

        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        today_times = []
        today_temps = []
        today_rain = []

        tomorrow_times = []
        tomorrow_temps = []
        tomorrow_rain = []

        for i, t in enumerate(hourly["time"]):
            if str(t).startswith(str(tomorrow)):
                tomorrow_times.append(t[11:16])
                tomorrow_temps.append(hourly["temperature_2m"][i])
                tomorrow_rain.append(hourly["precipitation_probability"][i])

        if not tomorrow_temps:
            return None

        return {
            "max": daily["temperature_2m_max"][1],
            "min": daily["temperature_2m_min"][1],
            "rain_max": daily["precipitation_probability_max"][1],
            "wind": daily["wind_speed_10m_max"][1],
            "times": tomorrow_times,
            "temps": tomorrow_temps,
            "rain_probs": tomorrow_rain,
            "avg_temp": sum(tomorrow_temps) / len(tomorrow_temps),
            "updated": datetime.now().strftime("%H:%M:%S")
        }

    # -------------------
    # UMBRELLA LOGIC
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

        st.error("No weather data available.")
    if om is None:
        st.stop()
 
    today_tab, tomorrow_tab = st.tabs(
    ["📍 Today", "🌦️ Tomorrow"]
)
    # -------------------
    # DATAFRAME FOR GRAPH
    # -------------------
    df = pd.DataFrame({
        "Hour": om["times"],
        "Temperature": om["temps"]
    })

    # -------------------
    # CUSTOM STYLE
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
        margin-bottom: 20px;
    }

    .row {
        display:flex;
        justify-content:space-between;
        padding:10px;
        border-radius:10px;
        margin-bottom:6px;
    }

    .hot {
        background: rgba(255,99,71,0.25);
    }

    .warm {
        background: rgba(255,165,0,0.25);
    }

    .cool {
        background: rgba(135,206,250,0.25);
    }

    .cold {
        background: rgba(70,130,180,0.25);
    }

    .rain {
        background: rgba(30,144,255,0.25);
    }

    </style>
    """, unsafe_allow_html=True)

    # -------------------
    # HEADER
    # -------------------
    st.title("🌦️ Kalamaria Weather")

    st.markdown(
        f"""
        <div class="big">{om['avg_temp']:.0f}°</div>
        <div class="sub">
            Tomorrow Forecast • Updated {om['updated']}
        </div>
        """,
        unsafe_allow_html=True
    )

    # -------------------
    # WEATHER STATUS
    # -------------------
    if om["rain_max"] >= 70:
        st.error("🌧️ Heavy rain likely tomorrow")

    elif om["rain_max"] >= 40:
        st.warning("🌦️ Possible showers tomorrow")

    else:
        st.success("☀️ Mostly dry weather expected")

    # -------------------
    # MAIN METRICS
    # -------------------
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "🌡️ Max Temperature",
            f"{om['max']:.1f}°C"
        )

        st.metric(
            "🌧️ Rain Chance",
            f"{om['rain_max']}%"
        )

    with col2:
        st.metric(
            "🌡️ Min Temperature",
            f"{om['min']:.1f}°C"
        )

        st.metric(
            "💨 Wind Speed",
            f"{om['wind']:.1f} km/h"
        )

    # -------------------
    # TEMPERATURE GRAPH
    # -------------------
    st.subheader("📊 Hourly Temperature")

    st.line_chart(
        df.set_index("Hour"),
        height=300
    )

    # -------------------
    # UMBRELLA SECTION
    # -------------------
    st.subheader("☂️ Umbrella Recommendation")

    blocks = detect_rain_blocks(
        om["times"],
        om["rain_probs"]
    )

    if not blocks:

        st.success(
            "No umbrella needed tomorrow 🌤️"
        )

    else:

        for block in blocks:

            start_time = om["times"][block[0]]
            end_time = om["times"][block[1]]

            max_rain = max(
                om["rain_probs"][block[0]:block[1]+1]
            )

            st.markdown(
                f"""
                <div class="row rain">
                    <div>☂️ {start_time} → {end_time}</div>
                    <div>{max_rain}% rain</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.warning(
            "Bring an umbrella during these periods ☂️"
        )

    # -------------------
    # HOURLY BREAKDOWN
    # -------------------
    with st.expander("🕐 Hourly Forecast"):

        for i in range(len(om["temps"])):

            temp = om["temps"][i]
            hour = om["times"][i]
            rain = om["rain_probs"][i]

            if temp >= 30:
                css_class = "row hot"

            elif temp >= 24:
                css_class = "row warm"

            elif temp >= 16:
                css_class = "row cool"

            else:
                css_class = "row cold"

            st.markdown(
                f"""
                <div class="{css_class}">
                    <div>{hour}</div>
                    <div>
                        {temp:.1f}°C • 🌧️ {rain}%
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    ```
