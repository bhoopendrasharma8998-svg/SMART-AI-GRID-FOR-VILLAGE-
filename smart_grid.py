import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components

# --- PAGE CONFIGURATION & CSS (LIGHT PINK THEME) ---
st.set_page_config(page_title="AI Smart Village Grid", page_icon="🌸", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #2c3e50; }
    h1, h2, h3 { color: #d81b60 !important; font-family: 'Segoe UI', Tahoma, sans-serif; }
    div[data-testid="metric-container"] {
        background: #fff0f5; border: 1px solid #f8bbd0; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
        border-radius: 12px; padding: 20px; transition: all 0.3s ease;
    }
    div[data-testid="metric-container"]:hover { transform: translateY(-3px); box-shadow: 0 6px 15px rgba(216, 27, 96, 0.15); }
    div[data-testid="metric-container"] label { color: #555555 !important; font-size: 15px !important; font-weight: bold; }
    div[data-testid="metric-container"] div { color: #d81b60 !important; }
    hr { border-color: #fce4ec; }
    [data-testid="stSidebar"] { background-color: #fafafa !important; border-right: 1px solid #fce4ec; }
    </style>
""", unsafe_allow_html=True)

# --- DYNAMIC SIMULATION LOGIC ---
@st.cache_data
def generate_base_houses():
    np.random.seed(42)
    return pd.DataFrame({
        'House_ID': [f"House_{i}" for i in range(1, 401)],
        'Max_Solar_Cap': np.random.uniform(2, 5, 400),
        'Battery_Max_Cap': np.random.uniform(3, 7, 400) # Battery size in kWh
    })

base_houses = generate_base_houses()

def calculate_current_status(hour, weather, temperature):
    df = base_houses.copy()
    
    # Solar Logic
    if hour < 6 or hour > 18:
        solar_multiplier = 0.0
    else:
        solar_multiplier = np.sin((hour - 6) * np.pi / 12) 
        
    if weather == "Cloudy": solar_multiplier *= 0.5
    elif weather == "Rainy": solar_multiplier *= 0.2
    
    df['Current_Solar_kWh'] = df['Max_Solar_Cap'] * solar_multiplier
    
    # Consumption Logic
    if 7 <= hour <= 10 or 18 <= hour <= 22:
        base_cons = np.random.uniform(1.5, 3.5, 400)
    elif 23 <= hour or hour <= 5:
        base_cons = np.random.uniform(0.2, 0.8, 400)
    else:
        base_cons = np.random.uniform(1.0, 2.5, 400)
        
    df['Consumption_kWh'] = base_cons
    
    # --- BATTERY & INVERTER LOGIC (NEW) ---
    # Simulate Battery Level based on time of day (Charges during day, drains at night)
    if 10 <= hour <= 16:
        df['Battery_Level_%'] = np.random.uniform(70, 100, 400)
    elif 17 <= hour <= 22:
        df['Battery_Level_%'] = np.random.uniform(40, 70, 400)
    else:
        df['Battery_Level_%'] = np.random.uniform(20, 40, 400) # 20% is minimum safe discharge
        
    df['Battery_Available_kWh'] = (df['Battery_Level_%'] / 100) * df['Battery_Max_Cap']
    
    # Net calculation per house
    df['Net_Before_Battery'] = df['Current_Solar_kWh'] - df['Consumption_kWh']
    
    # Final Surplus/Deficit calculation
    df['Surplus_For_Trade'] = np.where(df['Net_Before_Battery'] > 0, df['Net_Before_Battery'], 0)
    df['Deficit_After_Solar'] = np.where(df['Net_Before_Battery'] < 0, abs(df['Net_Before_Battery']), 0)
    
    return df

# --- SIDEBAR ---
st.sidebar.title("🌸 Grid Control Panel")

# LIVE CLOCK
components.html(
    """
    <div style="background: #fff0f5; padding: 15px; border-radius: 12px; text-align: center; border: 1px solid #f8bbd0;">
        <div style="color: #555555; font-size: 13px; font-weight: bold; margin-bottom: 5px;">LIVE GRID TIME</div>
        <span id="clock" style="color: #d81b60; font-size: 26px; font-family: monospace; font-weight: bold;"></span>
    </div>
    <script>
        function updateTime() {
            document.getElementById('clock').innerHTML = new Date().toLocaleTimeString('en-US');
        }
        setInterval(updateTime, 1000); updateTime();
    </script>
    """, height=90
)

st.sidebar.markdown("---")
st.sidebar.write("### 🎛️ AI Environment Settings")
selected_time = st.sidebar.slider("⏰ Simulation Time (Hour)", 0, 23, 13, format="%d:00")
weather = st.sidebar.selectbox("🌤️ Weather Condition", ["Sunny", "Cloudy", "Rainy"])
temp = st.sidebar.slider("🌡️ Temperature (°C)", 10, 50, 35)

# Calculate system-wide totals
df_live = calculate_current_status(selected_time, weather, temp)
total_demand = df_live['Consumption_kWh'].sum()
total_solar = df_live['Current_Solar_kWh'].sum()

# Battery usage calculation for the whole village
total_deficit_after_solar = df_live['Deficit_After_Solar'].sum()
usable_battery = df_live['Battery_Available_kWh'].sum() * 0.8 # Reserving 20% minimum battery

if total_deficit_after_solar > 0:
    battery_used = min(total_deficit_after_solar, usable_battery)
    remaining_deficit = total_deficit_after_solar - battery_used
else:
    battery_used = 0
    remaining_deficit = 0

# Biogas & Grid Backup logic
central_biogas_capacity = 500
biogas_used = min(central_biogas_capacity, remaining_deficit)
grid_usage = max(0, remaining_deficit - biogas_used)

st.sidebar.markdown("---")
menu = st.sidebar.radio("📌 Navigation Menu", ["🌸 Village Dashboard", "🏠 Individual Profile", "🧠 AI Energy Predictor"])

# ================= PAGE 1: VILLAGE DASHBOARD =================
if menu == "🌸 Village Dashboard":
    st.title(f"🌸 AI Smart Microgrid (Simulated at {selected_time}:00 Hrs)")
    
    # Active Source Indicator (NEW)
    if total_solar >= total_demand:
        active_state = "☀️ Running 100% on Solar (Batteries Charging)"
    elif total_solar + battery_used >= total_demand:
        active_state = "🔋 Running on Solar + Battery Inverters"
    elif biogas_used > 0 and grid_usage == 0:
        active_state = "♻️ Running on Battery + Central Biogas Backup"
    else:
        active_state = "🏢 Heavy Load: External Gov Grid Active"
        
    st.info(f"**⚡ Current Live Status:** {active_state}")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💡 Total Village Load", f"{total_demand:.1f} kWh")
    col2.metric("☀️ Active Solar", f"{total_solar:.1f} kWh")
    col3.metric("🔋 Inverter/Battery Active", f"{battery_used:.1f} kWh")
    col4.metric("♻️ Biogas / Grid Backup", f"{biogas_used + grid_usage:.1f} kWh")
    
    st.markdown("---")
    
    # Updated 3D Chart including Battery
    col_chart1, col_chart2 = st.columns([1, 1.5])
    with col_chart1:
        st.subheader("📊 Live Power Source Mix")
        labels = ['Rooftop Solar', 'Battery Inverters', 'Central Biogas', 'External Grid']
        values = [total_solar, battery_used, biogas_used, grid_usage]
        colors = ['#f48fb1', '#ce93d8', '#81c784', '#e57373'] # Pink, Purple (Battery), Green, Red
        
        fig1 = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5, marker=dict(colors=colors))])
        fig1.update_layout(paper_bgcolor='rgba(255,255,255,1)', font=dict(color='#2c3e50'), margin=dict(t=10, b=10))
        st.plotly_chart(fig1, use_container_width=True)
        
    with col_chart2:
        st.subheader("🏠 House Trading Status Map")
        df_live['Status'] = np.where(df_live['Surplus_For_Trade'] > 0, 'Surplus (Ready to Sell)', 'Deficit (Buying)')
        fig2 = px.scatter(df_live, x='Consumption_kWh', y='Current_Solar_kWh', color='Status',
                          color_discrete_map={'Surplus (Ready to Sell)': '#4caf50', 'Deficit (Buying)': '#d81b60'})
        fig2.update_layout(paper_bgcolor='rgba(255,255,255,1)', font=dict(color='#2c3e50'))
        st.plotly_chart(fig2, use_container_width=True)

# ================= PAGE 2: INDIVIDUAL PROFILE =================
elif menu == "🏠 Individual Profile":
    st.title("🏠 Smart Home Energy Profile")
    
    selected_house = st.selectbox("Search Your House", df_live['House_ID'][:100])
    my_data = df_live[df_live['House_ID'] == selected_house].iloc[0]
    
    c1, c2, c3 = st.columns(3)
    c1.info(f"⚡ Current Load:\n\n **{my_data['Consumption_kWh']:.2f} kWh**")
    c2.success(f"☀️ Solar Generating:\n\n **{my_data['Current_Solar_kWh']:.2f} kWh**")
    
    # Showing Battery Status Dynamically
    if my_data['Surplus_For_Trade'] > 0:
        batt_state = "⚡ Charging"
    elif my_data['Deficit_After_Solar'] > 0 and my_data['Battery_Level_%'] > 20:
        batt_state = "🔋 Discharging (Supplying House)"
    else:
        batt_state = "⚠️ Low (Standby)"
        
    c3.warning(f"🔋 Battery ({my_data['Battery_Level_%']:.0f}%):\n\n **{batt_state}**")
    
    st.markdown("---")
    if my_data['Surplus_For_Trade'] > 0:
        st.success(f"✅ **STATUS:** Your battery is charging, and you have **{my_data['Surplus_For_Trade']:.2f} kWh EXTRA** to sell via P2P Trading!")
    else:
        st.error(f"⚠️ **STATUS:** Solar is low. Inverter is running. Need extra {my_data['Deficit_After_Solar']:.2f} kWh from Village Grid.")

# ================= PAGE 3: AI PREDICTOR =================
elif menu == "🧠 AI Energy Predictor":
    st.title("🧠 AI Grid Intelligence Core")
    
    st.write(f"**Current Input:** Time: {selected_time}:00 | Weather: {weather}")
    st.markdown("---")
    
    st.subheader("Live Priority Routing Algorithm:")
    st.write("1️⃣ **Priority 1:** Rooftop Solar")
    st.write("2️⃣ **Priority 2:** House Battery Inverters")
    st.write("3️⃣ **Priority 3:** Central Biogas Plant")
    st.write("4️⃣ **Priority 4:** Gov Grid")
