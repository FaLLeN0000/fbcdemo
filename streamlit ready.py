import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="SSMC FBC Digital Twin", layout="wide")
st.title("Fluidized Bed Crystallization (FBC) - Process Control")
st.markdown("Adjust the factory parameters below to see how fluid dynamics and chemistry affect the CaF2 valorization process.")

# ==========================================
# 2. UI CONTROLS (SIDEBAR)
# ==========================================
st.sidebar.header("Process Controls")
hf_load = st.sidebar.slider("Incoming HF Load (ppm)", 1000, 3000, 2000, step=100)
ca_dose = st.sidebar.slider("Calcium Dosage", 0, 100, 50)
velocity = st.sidebar.slider("Upflow Velocity", 0, 100, 50)

st.sidebar.markdown("---")
st.sidebar.header("Visualization Toggles")
show_zone = st.sidebar.checkbox("Highlight Reaction Zone", value=False)
show_flow = st.sidebar.checkbox("Show Flow Dynamics", value=False)

# ==========================================
# 3. CORE SIMULATION ENGINE
# ==========================================
def calculate_state(hf, ca, vel):
    ca_error = ca - (hf / 2000) * 50
    vel_error = vel - 50
    
    # Calculate Yield
    yield_base = (hf / 2000) * 100 
    yield_penalty = (abs(ca_error) * 1.5) + (abs(vel_error) * 2.0)
    current_yield = max(0, yield_base - yield_penalty)
    
    # Calculate Effluent
    effluent_base = 5.0 
    effluent_penalty = (abs(vel_error) * 2) + (abs(ca_error) * 0.5)
    if ca_error < -5: effluent_penalty += abs(ca_error) * 3
    current_effluent = effluent_base + effluent_penalty
    
    # Determine Physical State
    if vel_error > 25: 
        state = "WASHOUT"
        msg = "WARNING: WASHOUT (Velocity too high)"
        color = 'red'
    elif ca_error > 25: 
        state = "SLUDGE"
        msg = "WARNING: SLUDGE (Homogeneous Nucleation)"
        color = 'orange'
    elif current_effluent <= 15 and current_yield > 80: 
        state = "OPTIMAL"
        msg = "OPTIMAL VALORIZATION (Pellets Growing)"
        color = 'green'
    else: 
        state = "SUB-OPTIMAL"
        msg = "SUB-OPTIMAL (Adjust Parameters)"
        color = 'gray'
        
    return current_effluent, current_yield, state, msg, color

eff, yld, state, status_msg, status_color = calculate_state(hf_load, ca_dose, velocity)

# ==========================================
# 4. DASHBOARD LAYOUT
# ==========================================
col1, col2 = st.columns([1, 1.5])

with col2:
    st.subheader("Real-Time Data Metrics")
    metric_col1, metric_col2 = st.columns(2)
    metric_col1.metric("Effluent HF (Limit: 15 ppm)", f"{eff:.1f} ppm", delta=f"{15 - eff:.1f} margin", delta_color="normal" if eff <= 15 else "inverse")
    metric_col2.metric("CaF2 Pellet Yield", f"{yld:.1f} kg/h")
    
    st.markdown(f"**System Status:** <span style='color:{status_color}; font-size:20px'>{status_msg}</span>", unsafe_allow_html=True)
    
    # Static Data Charts for context
    fig_charts, (ax_eff, ax_yld) = plt.subplots(2, 1, figsize=(8, 6))
    
    ax_eff.bar(["Current Effluent"], [eff], color='blue' if eff <=15 else 'red')
    ax_eff.axhline(y=15, color='red', linestyle='--', label='15 ppm Dump Limit')
    ax_eff.set_ylim(0, 50)
    ax_eff.set_ylabel('HF (ppm)')
    ax_eff.legend()
    
    ax_yld.bar(["Current Yield"], [yld], color='green')
    ax_yld.set_ylim(0, 120)
    ax_yld.set_ylabel('CaF2 (kg/h)')
    
    plt.tight_layout()
    st.pyplot(fig_charts)

with col1:
    st.subheader("Reactor Structure")
    
    fig_tank, ax_tank = plt.subplots(figsize=(6, 8))
    ax_tank.set_xlim(-0.2, 1.2) 
    ax_tank.set_ylim(-0.15, 1.15)
    ax_tank.axis('off')
    
    # Tank walls
    ax_tank.plot([0.2, 0.2, 0.45], [1.0, 0.2, 0.05], color='black', lw=4) 
    ax_tank.plot([0.8, 0.8, 0.55], [1.0, 0.2, 0.05], color='black', lw=4) 

    # Labels
    ax_tank.arrow(0.5, -0.12, 0, 0.1, head_width=0.03, color='blue', lw=2)
    ax_tank.text(0.5, -0.15, "HF Influent Inlet", ha='center', fontsize=12, fontweight='bold', color='blue')
    
    ax_tank.arrow(0.05, 0.25, 0.12, 0, head_width=0.02, color='purple', lw=2)
    ax_tank.text(0.03, 0.25, "Calcium\nInjection", ha='right', va='center', fontsize=12, fontweight='bold', color='purple')
    
    ax_tank.text(0.5, -0.02, "Pellet Harvest", ha='center', fontsize=12, fontweight='bold')
    ax_tank.text(0.5, 1.05, "⬆ Clean Effluent Out ⬆", ha='center', fontsize=12, fontweight='bold', color='#2980b9')
    
    if show_zone:
        ax_tank.axhspan(0.35, 0.65, color='gold', alpha=0.2)
        ax_tank.text(0.85, 0.5, "Metastable\nReaction Zone", color='darkgoldenrod', fontweight='bold', va='center', ha='left')

    if show_flow:
        # Draw flow vectors based on velocity
        flow_height = velocity / 100
        for i in np.linspace(0.25, 0.75, 5):
            ax_tank.arrow(i, 0.1, 0, flow_height * 0.8, head_width=0.02, color='cyan', alpha=0.5, lw=2)
            
    # Particle Physics Rendering
    np.random.seed(42) # Keep particles from flickering randomly
    num_particles = 150
    px = np.random.uniform(0.25, 0.75, num_particles)
    
    if state == "WASHOUT":
        py = np.random.uniform(0.6, 1.1, num_particles)
        psizes = np.random.uniform(10, 20, num_particles)
        pcolors = '#e74c3c'
    elif state == "SLUDGE":
        py = np.random.uniform(0.2, 0.8, num_particles)
        psizes = np.random.uniform(5, 15, num_particles)
        pcolors = 'gray'
    elif state == "OPTIMAL":
        py = np.random.uniform(0.1, 0.6, num_particles)
        # Particles lower in the tank are larger (simulating harvest growth)
        psizes = 100 * (1 - py) 
        pcolors = '#27ae60'
    else:
        py = np.random.uniform(0.3, 0.7, num_particles)
        psizes = np.random.uniform(10, 30, num_particles)
        pcolors = '#3498db'

    ax_tank.scatter(px, py, s=psizes, c=pcolors, alpha=0.8, edgecolors='black')
    
    st.pyplot(fig_tank)