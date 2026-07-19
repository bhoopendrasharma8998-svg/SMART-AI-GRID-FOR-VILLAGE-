import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components

st.set_page_config(page_title="AI Smart Village Grid", page_icon="🌸", layout="wide")


st.markdown("""
    <style>
    /* Main Background - Pure White */
    .stApp {
        background-color: #ffffff; 
        color: #2c3e50; /* Dark Gray for clear reading */
    }
    
    /* Soft Pink Headings */
    h1, h2, h3 {
        color: #d81b60 !important; /* Deep Pink */
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        text-shadow: none;
    }

    /* Metric Cards - Soft Light Pink */
    div[data-testid="metric-container"] {
        background: #fff0f5; /* LavenderBlush / Very Light Pink */
        border: 1px solid #f8bbd0; /* Soft Pink Border */
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05); /* Soft shadow */
        border-radius: 12px;
        padding: 20px;
        transition: all 0.3s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 15px rgba(216, 27, 96, 0.15);
    }
    
    /* Metric Text Colors */
    div[data-testid="metric-container"] label {
        color: #555555 !important; /* Dark Gray for labels */
        font-size: 15px !important;
        font-weight: bold;
    }
    div[data-testid="metric-container"] div {
        color: #d81b60 !important; /* Pink for the big numbers */
    }

    /* Custom Divider */
    hr {
        border-color: #fce4ec;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #fafafa !important; /* Very light gray sidebar */
        border-right: 1px solid #fce4ec;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_data
def generate_base_houses():
    np.random.seed(42)
    return pd.DataFrame({
        'House_ID': [f"House_{i}" for i in range(1, 401)],
        'Max_Solar_Cap': np.random.uniform(2, 5, 400),
        'Battery_Level_%': np.random.uniform(30, 100, 400)
    })

base_houses = generate_base_houses()

def calculate_current_status(hour, weather, temperature):
    df = base_houses.copy()
    
    if hour < 6 or hour > 18:
        solar_multiplier = 0.0
    else:
        solar_multiplier = np.sin((hour - 6) * np.pi / 12) 
        
    if weather == "Cloudy": solar_multiplier *= 0.5
    elif weather == "Rainy": solar_multiplier *= 0.2
    
    df['Current_Solar_kWh'] = df['Max_Solar_Cap'] * solar_multiplier
    
    if 7 <= hour <= 10 or 18 <= hour <= 22:
        base_cons = np.random.uniform(1.5, 3.5, 400)
    elif 23 <= hour or hour <= 5:
        base_cons = np.random.uniform(0.2, 0.8, 400)
    else:
        base_cons = np.random.uniform(1.0, 2.5, 400)
        
    df['Consumption_kWh'] = base_cons
    df['Net_Energy'] = df['Current_Solar_kWh'] - df['Consumption_kWh']
    return df


st.sidebar.title("🌸 Grid Control Panel")


components.html(
    """
    <div style="background: #fff0f5; padding: 15px; border-radius: 12px; text-align: center; border: 1px solid #f8bbd0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <div style="color: #555555; font-family: sans-serif; font-size: 13px; font-weight: bold; margin-bottom: 5px;">LIVE GRID TIME</div>
        <span id="clock" style="color: #d81b60; font-size: 26px; font-family: 'Courier New', Courier, monospace; font-weight: 900; letter-spacing: 2px;"></span>
    </div>
    <script>
        function updateTime() {
            var now = new Date();
            var timeString = now.toLocaleTimeString('en-US', {hour: '2-digit', minute:'2-digit', second:'2-digit', hour12: true});
            document.getElementById('clock').innerHTML = timeString;
        }
        setInterval(updateTime, 1000);
        updateTime();
    </script>
    """,
    height=100
)

st.sidebar.markdown("---")
st.sidebar.write("### 🎛️ AI Environment Settings")

selected_time = st.sidebar.slider("⏰ Simulation Time (Hour)", 0, 23, 13, format="%d:00")
weather = st.sidebar.selectbox("🌤️ Weather Condition", ["Sunny", "Cloudy", "Rainy"])
temp = st.sidebar.slider("🌡️ Temperature (°C)", 10, 50, 35)

df_live = calculate_current_status(selected_time, weather, temp)
total_village_demand = df_live['Consumption_kWh'].sum()
total_solar_gen = df_live['Current_Solar_kWh'].sum()
central_biogas_capacity = 500

if total_solar_gen < total_village_demand:
    biogas_used = min(central_biogas_capacity, total_village_demand - total_solar_gen)
else:
    biogas_used = 0

grid_usage = max(0, total_village_demand - (total_solar_gen + biogas_used))

st.sidebar.markdown("---")
menu = st.sidebar.radio("📌 Navigation Menu", ["🌸 Village Dashboard", "🏠 Individual Profile", "🧠 AI Energy Predictor", "🤝 Smart Trading"])


if menu == "🌸 Village Dashboard":
    st.title(f"🌸 Live Smart Village Grid (Simulated at {selected_time}:00 Hrs)")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💡 Total Load", f"{total_village_demand:.1f} kWh", "Demand")
    col2.metric("☀️ Solar Generation", f"{total_solar_gen:.1f} kWh", "Renewable")
    col3.metric("♻️ Biogas Active", f"{biogas_used:.1f} kWh", "Backup")
    col4.metric("🏢 Gov Grid Usage", f"{grid_usage:.1f} kWh", "External Dependency")
    
    st.markdown("---")
    
    st.subheader("📊 Live Power Distribution")
    col_chart1, col_chart2 = st.columns([1, 1.5])
    
    with col_chart1:
        
        labels = ['Rooftop Solar', 'Central Biogas', 'External Grid']
        values = [total_solar_gen, biogas_used, grid_usage]
        colors = ['#f48fb1', '#81c784', '#e57373'] # Soft Pink, Soft Green, Soft Red
        fig1 = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5, marker=dict(colors=colors))])
        fig1.update_layout(
            paper_bgcolor='rgba(255,255,255,1)', 
            plot_bgcolor='rgba(255,255,255,1)', 
            font=dict(color='#2c3e50'),
            margin=dict(t=30, b=10, l=10, r=10)
        )
        st.plotly_chart(fig1, use_container_width=True)
        
    with col_chart2:
        df_live['Status'] = np.where(df_live['Net_Energy'] >= 0, 'Surplus (Selling)', 'Deficit (Buying)')
        fig2 = px.scatter(df_live, x='Consumption_kWh', y='Current_Solar_kWh', color='Status',
                          color_discrete_map={'Surplus (Selling)': '#4caf50', 'Deficit (Buying)': '#d81b60'},
                          title="400 Houses Scatter Map")
        fig2.update_layout(
            paper_bgcolor='rgba(255,255,255,1)', 
            plot_bgcolor='rgba(255,255,255,1)', 
            font=dict(color='#2c3e50'),
            xaxis=dict(showgrid=True, gridcolor='#fce4ec'),
            yaxis=dict(showgrid=True, gridcolor='#fce4ec')
        )
        st.plotly_chart(fig2, use_container_width=True)


elif menu == "🏠 Individual Profile":
    st.title("🏠 Smart Home Energy Profile")
    
    selected_house = st.selectbox("Select Your House to View Dashboard", df_live['House_ID'][:100])
    my_data = df_live[df_live['House_ID'] == selected_house].iloc[0]
    
    st.markdown("### 📊 Real-time Analytics")
    c1, c2, c3 = st.columns(3)
    c1.info(f"⚡ Current Load:\n\n **{my_data['Consumption_kWh']:.2f} kWh**")
    c2.success(f"☀️ Solar Active:\n\n **{my_data['Current_Solar_kWh']:.2f} kWh**")
    c3.warning(f"🔋 Battery Status:\n\n **{my_data['Battery_Level_%']:.0f}%**")
    
    st.markdown("---")
    net_val = my_data['Net_Energy']
    if net_val > 0:
        st.success(f"✅ **STATUS: SURPLUS** | Generating {net_val:.2f} kWh EXTRA. Head to Smart Trading to sell.")
    else:
        st.error(f"⚠️ **STATUS: DEFICIT** | Short by {abs(net_val):.2f} kWh. Drawing power from Central Grid.")
    
    csv = pd.DataFrame([my_data]).to_csv(index=False)
    st.download_button(label="📥 Download Log (CSV)", data=csv, file_name=f"{selected_house}_live.csv", mime="text/csv")


elif menu == "🧠 AI Energy Predictor":
    st.title("🧠 AI Grid Intelligence Core")
    
    st.write(f"**Analyzing Sensor Data:** ⏰ Time: {selected_time}:00 | 🌤️ Weather: {weather} | 🌡️ Temp: {temp}°C")
    st.markdown("---")
    
    if selected_time < 6 or selected_time > 18:
        st.info("### 🌙 NIGHT MODE PROTOCOL")
        st.write("> Solar output is 0. Central Biogas Plant instructed to handle baseload. House batteries are discharging to optimize grid stability.")
    elif weather == "Sunny":
        st.success("### ☀️ PEAK RENEWABLE PROTOCOL")
        st.write("> Maximum solar generation detected. Central Biogas powered down to standby. Excess energy routing to local battery storage.")
    elif weather in ["Cloudy", "Rainy"]:
        st.warning("### ☁️ LOW YIELD PROTOCOL")
        st.write("> Solar generation impacted by weather. Central Biogas output increased by 80% to prevent external grid reliance.")


elif menu == "🤝 Smart Trading":
    st.title("🤝 Decentralized Energy Trading")
    
    tab1, tab2 = st.tabs(["👥 Peer-to-Peer (P2P)", "🏢 Village to Government"])
    
    with tab1:
        st.subheader("Sell Your Extra Energy Directly to Neighbors")
        sellers = df_live[df_live['Net_Energy'] > 0]['House_ID'].tolist()
        if sellers:
            seller = st.selectbox("Select Your Account (Seller)", sellers[:30])
            surplus = df_live[df_live['House_ID'] == seller]['Net_Energy'].values[0]
            st.write(f"**Available for Trade:** {surplus:.2f} kWh")
            
            buyers = df_live[df_live['Net_Energy'] < 0]['House_ID'].tolist()
            buyer = st.selectbox("Select Buyer (Neighbor)", buyers[:30])
            
            if st.button("Initiate Blockchain Trade ⚡"):
                st.balloons()
                st.success(f"✅ Transaction Confirmed! {surplus:.2f} kWh routed from {seller} to {buyer}.")
        else:
            st.error("No surplus energy available in the village right now.")
            
    with tab2:
        st.subheader("Sell Central Biogas Surplus to Government Grid")
        if total_solar_gen > total_village_demand:
            st.success(f"Village is fully self-sustaining on Solar! Central Biogas capacity ({central_biogas_capacity} kWh) is available for export.")
            if st.button("Export to Gov Grid 🏢"):
                revenue = central_biogas_capacity * 5.50
                st.success(f"✅ Export Successful! Panchayat Earned: ₹ {revenue:.2f}")
        else:
            st.warning("Village is currently consuming Central Biogas power. Export restricted.")