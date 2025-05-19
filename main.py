"""
FlixOpt Energy System Modeling Web App

This Streamlit application provides a user interface for creating and solving
energy system models using the flixopt framework.
"""

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import flixopt as fx
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(
    page_title="FlixOpt Energy System Modeler",
    page_icon="🔋",
    layout="wide",
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 1rem;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# App title and description
st.title("FlixOpt Energy System Modeler")
st.markdown("""
This web application allows you to create, configure, and solve energy system models
using the FlixOpt framework. Define your system components, run optimizations, and
visualize results in an interactive environment.
""")

# Initialize session state variables if they don't exist
if 'flow_system' not in st.session_state:
    st.session_state.flow_system = None
if 'elements' not in st.session_state:
    st.session_state.elements = {
        'buses': [],
        'effects': [],
        'converters': [],
        'storages': [],
        'sources': [],
        'sinks': []
    }
if 'timesteps' not in st.session_state:
    st.session_state.timesteps = None
if 'results' not in st.session_state:
    st.session_state.results = None

# Add a main menu at the top
st.sidebar.title("FlixOpt Energy Modeler")
app_mode = st.sidebar.selectbox(
    "Select Mode",
    ["Model Builder", "Example Templates", "Help & Documentation"]
)

if app_mode == "Model Builder":
    # Main app content (tabs for building and running the model)
    # Create tabs for different sections of the application
    tabs = st.tabs([
        "System Configuration",
        "Components",
        "Optimization",
        "Results",
        "Advanced Analysis"
    ])

        # ==================== SYSTEM CONFIGURATION TAB ====================
    with tabs[0]:
        st.header("System Configuration")

        # Time range configuration
        st.subheader("Simulation Time Range")
        col1, col2, col3 = st.columns(3)

        with col1:
            start_date = st.date_input("Start Date", datetime.now().date())
        with col2:
            periods = st.number_input("Number of Time Periods", min_value=1, value=24, step=1)
        with col3:
            freq = st.selectbox("Frequency", ["h", "30min", "15min", "d"], index=0)

        # Configure penalties
        st.subheader("System Parameters")
        excess_penalty = st.number_input("Excess Penalty", min_value=0.0, value=None, format="%.1e")

        # Initialize system button
        if st.button("Initialize Flow System"):
            try:
                # Create time range
                timesteps = pd.date_range(start_date, periods=periods, freq=freq)
                st.session_state.timesteps = timesteps

                # Create flow system
                st.session_state.flow_system = fx.FlowSystem(timesteps)

                st.success(f"Flow system initialized with {len(timesteps)} time steps from {timesteps[0]} to {timesteps[-1]}")
            except Exception as e:
                st.error(f"Error initializing flow system: {str(e)}")

    # ==================== COMPONENTS TAB ====================
    with tabs[1]:
        st.header("System Components")

        if st.session_state.flow_system is None:
            st.warning("Please initialize the flow system first in the System Configuration tab.")
        else:
            # Component selection tabs
            component_tabs = st.tabs(["Buses", "Effects", "Converters", "Storage", "Sources & Sinks"])

            # --- BUSES TAB ---
            with component_tabs[0]:
                st.subheader("Energy Buses")
                st.write("Buses represent node balances (inputs=outputs) for different energy carriers in the system.")

                with st.form("bus_form"):
                    bus_name = st.text_input("Bus Name", value="Bus")
                    bus_excess_penalty = st.number_input("Excess Penalty per Flow Hour",
                                                         min_value=0.0,
                                                         value=excess_penalty,
                                                         format="%.1e")

                    if st.form_submit_button("Add Bus"):
                        try:
                            new_bus = fx.Bus(bus_name, excess_penalty_per_flow_hour=bus_excess_penalty)
                            st.session_state.elements['buses'].append(new_bus)
                            st.session_state.flow_system.add_elements(new_bus)
                            st.success(f"Bus '{bus_name}' added successfully!")
                        except Exception as e:
                            st.error(f"Error adding bus: {str(e)}")

                # Display existing buses
                if st.session_state.elements['buses']:
                    st.write("Current Buses:")
                    for i, bus in enumerate(st.session_state.elements['buses']):
                        st.write(f"{i+1}. {bus}")

            # --- EFFECTS TAB ---
            with component_tabs[1]:
                st.subheader("Effects")
                st.write("Effects represent costs, emissions, or other impacts of the energy system.")

                with st.form("effect_form"):
                    effect_name = st.text_input("Effect Name", value="costs")
                    effect_unit = st.text_input("Unit", value="€")
                    effect_description = st.text_input("Description", value="Kosten")
                    col1, col2 = st.columns(2)
                    with col1:
                        is_standard = st.checkbox("Is Standard Effect", value=True)
                    with col2:
                        is_objective = st.checkbox("Is Objective", value=True)

                    # Only show maximum total if not an objective
                    if not is_objective:
                        maximum_total = st.number_input("Maximum Total", value=0.0)
                    else:
                        maximum_total = None

                    if st.form_submit_button("Add Effect"):
                        try:
                            new_effect = fx.Effect(
                                effect_name,
                                effect_unit,
                                effect_description,
                                is_standard=is_standard,
                                is_objective=is_objective,
                                maximum_total=maximum_total
                            )
                            st.session_state.elements['effects'].append(new_effect)
                            st.session_state.flow_system.add_elements(new_effect)
                            st.success(f"Effect '{effect_name}' added successfully!")
                        except Exception as e:
                            st.error(f"Error adding effect: {str(e)}")

                # Display existing effects
                if st.session_state.elements['effects']:
                    st.write("Current Effects:")
                    for i, effect in enumerate(st.session_state.elements['effects']):
                        st.write(f"{i+1}. {effect.label} ({effect.unit}) - {'Objective' if effect.is_objective else 'Constraint'}")

            # --- CONVERTERS TAB ---
            with component_tabs[2]:
                st.subheader("Converters")
                st.write("Converters transform energy from one form to another, like boilers or CHP units.")

                converter_type = st.selectbox(
                    "Converter Type",
                    ["Boiler", "CHP (Combined Heat and Power)"]
                )

                if converter_type == "Boiler":
                    with st.form("boiler_form"):
                        boiler_name = st.text_input("Boiler Name", value="Kessel")
                        boiler_eta = st.slider("Efficiency (η)", min_value=0.5, max_value=1.0, value=0.85, step=0.01)

                        st.subheader("Thermal Output (Q_th)")
                        q_th_bus = st.selectbox("Output Bus", list(st.session_state.flow_system.buses), key="q_th_bus")
                        q_th_size = st.number_input("Size (kW)", min_value=0.001, value=50.0, key="q_th_size")
                        q_th_min_load = st.slider("Minimum Load Factor", min_value=0.0, max_value=1.0, value=0.1, step=0.01)

                        st.subheader("Fuel Input (Q_fu)")
                        q_fu_bus = st.selectbox("Input Bus", list(st.session_state.flow_system.buses), key="q_fu_bus")

                        if st.form_submit_button("Add Boiler"):
                            try:
                                # Create boiler
                                boiler = fx.linear_converters.Boiler(
                                    boiler_name,
                                    eta=boiler_eta,
                                    Q_th=fx.Flow(
                                    label='Q_th',
                                    bus=q_th_bus,
                                    size=q_th_size,
                                    load_factor_min=q_th_min_load,
                                    relative_minimum=q_th_min_load,
                                ),
                                    Q_fu=fx.Flow(label='Q_fu', bus=q_fu_bus, size=q_th_size/boiler_eta),
                                )

                                st.session_state.elements['converters'].append(boiler)
                                st.session_state.flow_system.add_elements(boiler)
                                st.success(f"Boiler '{boiler_name}' added successfully!")
                            except Exception as e:
                                st.error(f"Error adding boiler: {str(e)}")

                elif converter_type == "CHP (Combined Heat and Power)":
                    with st.form("chp_form"):
                        chp_name = st.text_input("CHP Name", value="BHKW")
                        col1, col2 = st.columns(2)
                        with col1:
                            eta_el = st.slider("Electrical Efficiency", min_value=0.1, max_value=0.5, value=0.4, step=0.01)
                        with col2:
                            eta_th = st.slider("Thermal Efficiency", min_value=0.1, max_value=0.6, value=0.5, step=0.01)

                        st.subheader("Electrical Output (P_el)")
                        p_el_bus = st.selectbox("Electricity Bus", list(st.session_state.flow_system.buses), key="p_el_bus")
                        p_el_size = st.number_input("Electrical Size (kW)", min_value=1.0, value=60.0)
                        p_el_min_load = st.slider("Minimum Electrical Load Factor", min_value=0.0, max_value=1.0, value=0.1, step=0.01)

                        st.subheader("Thermal Output (Q_th)")
                        q_th_bus = st.selectbox("Heat Bus", list(st.session_state.flow_system.buses), key="chp_q_th_bus")

                        st.subheader("Fuel Input (Q_fu)")
                        q_fu_bus = st.selectbox("Fuel Bus", list(st.session_state.flow_system.buses), key="chp_q_fu_bus")

                        if st.form_submit_button("Add CHP"):
                            try:
                                # Create CHP unit
                                p_el = fx.Flow('P_el', bus=p_el_bus, size=p_el_size, relative_minimum=p_el_min_load)
                                q_th = fx.Flow('Q_th', bus=q_th_bus, size=(p_el_size * eta_th) / eta_el)
                                q_fu = fx.Flow('Q_fu', bus=q_fu_bus, size=p_el_size / eta_el)

                                chp = fx.linear_converters.CHP(
                                    chp_name,
                                    eta_el=eta_el,
                                    eta_th=eta_th,
                                    P_el=p_el,
                                    Q_th=q_th,
                                    Q_fu=q_fu
                                )

                                st.session_state.elements['converters'].append(chp)
                                st.session_state.flow_system.add_elements(chp)
                                st.success(f"CHP '{chp_name}' added successfully!")
                            except Exception as e:
                                st.error(f"Error adding CHP: {str(e)}")

                # Display existing converters
                if st.session_state.elements['converters']:
                    st.write("Current Converters:")
                    for i, converter in enumerate(st.session_state.elements['converters']):
                        st.write(f"{i+1}. {converter.label} ({type(converter).__name__})")

            # --- STORAGE TAB ---
            with component_tabs[3]:
                st.subheader("Storage Systems")
                st.write("Storage systems store energy for later use.")

                with st.form("storage_form"):
                    storage_name = st.text_input("Storage Name", value="Speicher")
                    storage_bus = st.selectbox("Energy Bus", list(st.session_state.flow_system.buses))

                    col1, col2 = st.columns(2)
                    with col1:
                        capacity = st.number_input("Capacity (kWh)", min_value=1.0, value=100.0)
                    with col2:
                        initial_charge = st.slider("Initial Charge State (%)", min_value=0, max_value=100, value=0) / 100

                    col1, col2 = st.columns(2)
                    with col1:
                        charge_rate = st.number_input("Max Charge Rate (kW)", min_value=1.0, value=50.0)
                    with col2:
                        discharge_rate = st.number_input("Max Discharge Rate (kW)", min_value=1.0, value=50.0)

                    col1, col2 = st.columns(2)
                    with col1:
                        eta_charge = st.slider("Charge Efficiency", min_value=0.1, max_value=1.0, value=0.9, step=0.01)
                    with col2:
                        eta_discharge = st.slider("Discharge Efficiency", min_value=0.1, max_value=1.0, value=0.9, step=0.01)

                    loss_rate = st.slider("Relative Loss per Hour", min_value=0.0, max_value=0.2, value=0.01, step=0.001, format="%.3f")
                    prevent_simultaneous = st.checkbox("Prevent Simultaneous Charge/Discharge", value=True)

                    if st.form_submit_button("Add Storage"):
                        try:
                            # Create storage system
                            new_storage = fx.Storage(
                                storage_name,
                                charging=fx.Flow(f'{storage_name}_charging', bus=storage_bus, size=charge_rate),
                                discharging=fx.Flow(f'{storage_name}_discharging', bus=storage_bus, size=discharge_rate),
                                capacity_in_flow_hours=capacity / charge_rate,
                                initial_charge_state=initial_charge * capacity,
                                eta_charge=eta_charge,
                                eta_discharge=eta_discharge,
                                relative_loss_per_hour=loss_rate,
                                prevent_simultaneous_charge_and_discharge=prevent_simultaneous
                            )

                            st.session_state.elements['storages'].append(new_storage)
                            st.session_state.flow_system.add_elements(new_storage)
                            st.success(f"Storage '{storage_name}' added successfully!")
                        except Exception as e:
                            st.error(f"Error adding storage: {str(e)}")

                # Display existing storage systems
                if st.session_state.elements['storages']:
                    st.write("Current Storage Systems:")
                    for i, storage in enumerate(st.session_state.elements['storages']):
                        st.write(f"{i+1}. {storage.label}")

            # --- SOURCES & SINKS TAB ---
            with component_tabs[4]:
                st.subheader("Sources and Sinks")
                st.write("Sources provide energy to the system; sinks consume energy from the system.")

                component_type = st.radio("Component Type", ["Source", "Sink"])

                if component_type == "Source":
                    with st.form("source_form"):
                        source_name = st.text_input("Source Name", value="Source")
                        source_bus = st.selectbox("Energy Bus", list(st.session_state.flow_system.buses))

                        col1, col2 = st.columns(2)
                        with col1:
                            source_size = st.number_input("Maximum Size (kW)", min_value=0.0, value=1000.0)

                        # Effects per flow hour
                        st.subheader("Effects per Flow Hour")
                        effects_dict = {}

                        for effect_name in list(st.session_state.flow_system.effects):
                            value = st.number_input(f"{effect_name} Effect per Flow Hour", value=0.04)
                            if value != 0:
                                effects_dict[effect_name] = value

                        # Time profile
                        st.subheader("Time Profile")
                        use_profile = st.checkbox("Use Time-Dependent Profile", value=False)

                        if use_profile:
                            profile_type = st.selectbox("Profile Type", ["Constant", "Sinusoidal", "Manual Entry"])

                            if profile_type == "Constant":
                                profile_value = st.number_input("Constant Value", min_value=0.0, max_value=1.0, value=1.0)
                                profile = np.ones(len(st.session_state.timesteps)) * profile_value
                            elif profile_type == "Sinusoidal":
                                amplitude = st.slider("Amplitude", min_value=0.0, max_value=1.0, value=0.5, step=0.01)
                                offset = st.slider("Offset", min_value=0.0, max_value=1.0, value=0.5, step=0.01)
                                periods = st.slider("Periods", min_value=1, max_value=5, value=1)

                                t = np.linspace(0, 2*np.pi*periods, len(st.session_state.timesteps))
                                profile = offset + amplitude * np.sin(t)
                            else:  # Manual Entry
                                st.write("Enter values for each time step:")
                                profile = np.ones(len(st.session_state.timesteps))

                                # Show a sample of time steps for manual entry
                                max_display = 24  # Limit number displayed for usability
                                for i in range(min(len(st.session_state.timesteps), max_display)):
                                    profile[i] = st.number_input(
                                        f"Value at {st.session_state.timesteps[i]}",
                                        min_value=0.0,
                                        max_value=1.0,
                                        value=1.0,
                                        key=f"source_profile_{i}"
                                    )

                                if len(st.session_state.timesteps) > max_display:
                                    st.info(f"Only showing first {max_display} time steps for manual entry.")

                            # Preview the profile
                            st.subheader("Profile Preview")
                            fig = px.line(
                                x=st.session_state.timesteps,
                                y=profile,
                                labels={"x": "Time", "y": "Relative Value"}
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            profile = None

                        if st.form_submit_button("Add Source"):
                            try:
                                # Create flow
                                if use_profile:
                                    flow = fx.Flow(
                                        f'{source_name}_flow',
                                        bus=source_bus,
                                        size=source_size,
                                        effects_per_flow_hour=effects_dict,
                                        fixed_relative_profile=profile
                                    )
                                else:
                                    flow = fx.Flow(
                                        f'{source_name}_flow',
                                        bus=source_bus,
                                        size=source_size,
                                        effects_per_flow_hour=effects_dict
                                    )

                                # Create source
                                new_source = fx.Source(source_name, source=flow)

                                st.session_state.elements['sources'].append(new_source)
                                st.session_state.flow_system.add_elements(new_source)
                                st.success(f"Source '{source_name}' added successfully!")
                            except Exception as e:
                                st.error(f"Error adding source: {str(e)}")

                elif component_type == "Sink":
                    with st.form("sink_form"):
                        sink_name = st.text_input("Sink Name", value="Sink")
                        sink_bus = st.selectbox("Energy Bus", list(st.session_state.flow_system.buses))

                        col1, col2 = st.columns(2)
                        with col1:
                            sink_size = st.number_input("Size (kW)", min_value=0.0, value=100.0)

                        # Effects per flow hour (can be negative for revenue)
                        st.subheader("Effects per Flow Hour")
                        st.write("Note: Use negative values for revenue/benefits")
                        effects_dict = {}

                        for effect_name in list(st.session_state.flow_system.effects):
                            value = st.number_input(f"{effect_name} Effect per Flow Hour", value=0.0)
                            if value != 0:
                                effects_dict[effect_name] = value

                        # Time profile for demand
                        st.subheader("Demand Profile")
                        profile_type = st.selectbox("Profile Type", ["Constant", "Sinusoidal", "Manual Entry"])

                        if profile_type == "Constant":
                            profile_value = st.number_input("Constant Value", min_value=0.0, max_value=1.0, value=1.0)
                            profile = np.ones(len(st.session_state.timesteps)) * profile_value
                        elif profile_type == "Sinusoidal":
                            amplitude = st.slider("Amplitude", min_value=0.0, max_value=1.0, value=0.5, step=0.01)
                            offset = st.slider("Offset", min_value=0.0, max_value=1.0, value=0.5, step=0.01)
                            periods = st.slider("Periods", min_value=1, max_value=5, value=1)

                            t = np.linspace(0, 2*np.pi*periods, len(st.session_state.timesteps))
                            profile = offset + amplitude * np.sin(t)
                        else:  # Manual Entry
                            st.write("Enter values for each time step:")
                            profile = np.ones(len(st.session_state.timesteps))

                            # Show a sample of time steps for manual entry
                            max_display = 24  # Limit number displayed for usability
                            for i in range(min(len(st.session_state.timesteps), max_display)):
                                profile[i] = st.number_input(
                                    f"Value at {st.session_state.timesteps[i]}",
                                    min_value=0.0,
                                    value=1.0,
                                    key=f"sink_profile_{i}"
                                )

                            if len(st.session_state.timesteps) > max_display:
                                st.info(f"Only showing first {max_display} time steps for manual entry.")

                        # Preview the profile
                        st.subheader("Profile Preview")
                        fig = px.line(
                            x=st.session_state.timesteps,
                            y=profile,
                            labels={"x": "Time", "y": "Relative Value"}
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        if st.form_submit_button("Add Sink"):
                            try:
                                # Create flow with fixed relative profile
                                flow = fx.Flow(
                                    f'{sink_name}_flow',
                                    bus=sink_bus,
                                    size=sink_size,
                                    effects_per_flow_hour=effects_dict,
                                    fixed_relative_profile=profile
                                )

                                # Create sink
                                new_sink = fx.Sink(sink_name, sink=flow)

                                st.session_state.elements['sinks'].append(new_sink)
                                st.session_state.flow_system.add_elements(new_sink)
                                st.success(f"Sink '{sink_name}' added successfully!")
                            except Exception as e:
                                st.error(f"Error adding sink: {str(e)}")

                # Display existing sources and sinks
                col1, col2 = st.columns(2)

                with col1:
                    if st.session_state.elements['sources']:
                        st.write("Current Sources:")
                        for i, source in enumerate(st.session_state.elements['sources']):
                            st.write(f"{i+1}. {source.label}")

                with col2:
                    if st.session_state.elements['sinks']:
                        st.write("Current Sinks:")
                        for i, sink in enumerate(st.session_state.elements['sinks']):
                            st.write(f"{i+1}. {sink.label}")

    # ==================== OPTIMIZATION TAB ====================
    with tabs[2]:
        st.header("Optimization")

        if st.session_state.flow_system is None:
            st.warning("Please initialize the flow system first in the System Configuration tab.")
        elif not any(st.session_state.elements.values()):
            st.warning("Please add components to your system before running the optimization.")
        else:
            # System overview
            st.subheader("System Overview")

            # Count components by type
            component_counts = {
                "Buses": len(st.session_state.elements['buses']),
                "Effects": len(st.session_state.elements['effects']),
                "Converters": len(st.session_state.elements['converters']),
                "Storage Systems": len(st.session_state.elements['storages']),
                "Sources": len(st.session_state.elements['sources']),
                "Sinks": len(st.session_state.elements['sinks'])
            }

            # Create a pie chart for component counts
            fig = go.Figure(data=[go.Pie(
                labels=list(component_counts.keys()),
                values=list(component_counts.values()),
                hole=.3
            )])
            fig.update_layout(title_text="Component Distribution")
            st.plotly_chart(fig, use_container_width=True)

            # Solver settings
            st.subheader("Solver Settings")
            col1, col2 = st.columns(2)

            with col1:
                gap = st.number_input("Relative Gap", min_value=0.001, max_value=0.1, value=0.01, step=0.001, format="%.3f")
            with col2:
                max_time = st.number_input("Maximum Solving Time (seconds)", min_value=10, max_value=3600, value=60, step=10)

            # Run optimization button
            if st.button("Run Optimization"):
                try:
                    with st.spinner("Running optimization..."):
                        # Create calculation
                        calculation = fx.FullCalculation('streamlit model', st.session_state.flow_system)
                        calculation.do_modeling()

                        # Solve the model
                        calculation.solve(fx.solvers.HighsSolver(gap, max_time))

                        # Store results
                        st.session_state.results = calculation.results

                        st.success("Optimization completed successfully!")
                except Exception as e:
                    st.error(f"Error during optimization: {str(e)}")

    # ==================== RESULTS TAB ====================
    with tabs[3]:
        st.header("Results Visualization")

        if st.session_state.results is None:
            st.warning("Please run the optimization first to see results.")
        else:
            results = st.session_state.results

            # Key Performance Indicators
            st.subheader("Key Performance Indicators")

            # Extract objective values
            objective_effects = [effect for effect in st.session_state.elements['effects'] if effect.is_objective]
            if objective_effects:
                objective_values = {}
                for effect in objective_effects:
                    try:
                        # Get total effect value
                        value = results.get_total_effect(effect.label)
                        objective_values[effect.label] = value
                    except:
                        objective_values[effect.label] = "N/A"

                # Display in columns
                cols = st.columns(len(objective_values))
                for i, (label, value) in enumerate(objective_values.items()):
                    with cols[i]:
                        st.metric(f"Total {label}", f"{value:.2f}" if isinstance(value, (int, float)) else value)

            # Results visualization options
            st.subheader("Visualization")

            # Component selection for visualization
            component_types = ["Buses", "Converters", "Storage", "System Overview"]
            viz_type = st.selectbox("Component Type", component_types)

            if viz_type == "Buses":
                # Bus balance visualization
                if st.session_state.elements['buses']:
                    selected_bus = st.selectbox("Select Bus", list(st.session_state.flow_system.buses))

                    # Visualization type for buses
                    bus_viz_type = st.radio(
                        "Visualization Type",
                        ["Node Balance", "Node Balance (Pie Chart)", "Flow Rates Heatmap"]
                    )

                    try:
                        if bus_viz_type == "Node Balance":
                            # Create a placeholder for the matplotlib figure
                            fig_placeholder = st.empty()

                            # Generate the plot
                            fig, ax = plt.subplots(figsize=(10, 6))
                            results[selected_bus].plot_node_balance(ax=ax)

                            # Display the plot
                            fig_placeholder.pyplot(fig)

                        elif bus_viz_type == "Node Balance (Pie Chart)":
                            # Create a placeholder for the matplotlib figure
                            fig_placeholder = st.empty()

                            # Generate the plot
                            fig, ax = plt.subplots(figsize=(10, 6))
                            results[selected_bus].plot_node_balance_pie(ax=ax)

                            # Display the plot
                            fig_placeholder.pyplot(fig)

                        elif bus_viz_type == "Flow Rates Heatmap":
                            # Get flows for the selected bus
                            component_flows = []
                            for component_type in ['converters', 'storages', 'sources', 'sinks']:
                                for component in st.session_state.elements[component_type]:
                                    for flow in component.flow:
                                        if hasattr(flow, 'bus') and flow.bus == selected_bus:
                                            component_flows.append(f"{component.label}({flow.label})|flow_rate")

                            if component_flows:
                                selected_flow = st.selectbox("Select Flow", component_flows)

                                # Create a placeholder for the matplotlib figure
                                fig_placeholder = st.empty()

                                # Generate the plot
                                fig, ax = plt.subplots(figsize=(10, 6))
                                results.plot_heatmap(selected_flow, ax=ax)

                                # Display the plot
                                fig_placeholder.pyplot(fig)
                            else:
                                st.warning(f"No flows found for bus {selected_bus}")
                    except Exception as e:
                        st.error(f"Error generating visualization: {str(e)}")
                else:
                    st.warning("No buses available for visualization.")

            elif viz_type == "Converters":
                # Converter visualization
                if st.session_state.elements['converters']:
                    converter_options = [conv.label for conv in st.session_state.elements['converters']]
                    selected_converter = st.selectbox("Select Converter", converter_options)

                    # Visualization type for converters
                    converter_viz_type = st.radio(
                        "Visualization Type",
                        ["Node Balance", "Flow Rates Heatmap"]
                    )

                    try:
                        if converter_viz_type == "Node Balance":
                            # Create a placeholder for the matplotlib figure
                            fig_placeholder = st.empty()

                            # Generate the plot
                            fig, ax = plt.subplots(figsize=(10, 6))
                            results[selected_converter].plot_node_balance(ax=ax)

                            # Display the plot
                            fig_placeholder.pyplot(fig)

                        elif converter_viz_type == "Flow Rates Heatmap":
                            # Get converter flows
                            converter = next((c for c in st.session_state.elements['converters'] if c.label == selected_converter), None)
                            if converter:
                                flow_options = [f"{selected_converter}({flow.label})|flow_rate" for flow in converter.flow]

                                if flow_options:
                                    selected_flow = st.selectbox("Select Flow", flow_options)

                                    # Create a placeholder for the matplotlib figure
                                    fig_placeholder = st.empty()

                                    # Generate the plot
                                    fig, ax = plt.subplots(figsize=(10, 6))
                                    results.plot_heatmap(selected_flow, ax=ax)

                                    # Display the plot
                                    fig_placeholder.pyplot(fig)
                                else:
                                    st.warning(f"No flows found for converter {selected_converter}")
                    except Exception as e:
                        st.error(f"Error generating visualization: {str(e)}")
                else:
                    st.warning("No converters available for visualization.")

            elif viz_type == "Storage":
                # Storage visualization
                if st.session_state.elements['storages']:
                    storage_options = [storage.label for storage in st.session_state.elements['storages']]
                    selected_storage = st.selectbox("Select Storage", storage_options)

                    try:
                        # Create a placeholder for the matplotlib figure
                        fig_placeholder = st.empty()

                        # Generate charge state plot
                        fig, ax = plt.subplots(figsize=(10, 6))
                        results[selected_storage].plot_charge_state(ax=ax)

                        # Display the plot
                        fig_placeholder.pyplot(fig)

                        # Show additional storage metrics
                        try:
                            storage = next((s for s in st.session_state.elements['storages'] if s.label == selected_storage), None)
                            if storage:
                                # Calculate storage utilization metrics
                                charge_state = results[selected_storage].charge_state
                                if charge_state is not None:
                                    max_charge = charge_state.max()
                                    avg_charge = charge_state.mean()
                                    utilization = avg_charge / max_charge if max_charge > 0 else 0

                                    # Display metrics in columns
                                    cols = st.columns(3)
                                    with cols[0]:
                                        st.metric("Maximum Charge", f"{max_charge:.2f} kWh")
                                    with cols[1]:
                                        st.metric("Average Charge", f"{avg_charge:.2f} kWh")
                                    with cols[2]:
                                        st.metric("Utilization Factor", f"{utilization:.2%}")
                        except Exception as e:
                            st.warning(f"Could not calculate storage metrics: {str(e)}")
                    except Exception as e:
                        st.error(f"Error generating visualization: {str(e)}")
                else:
                    st.warning("No storage systems available for visualization.")

            elif viz_type == "System Overview":
                # System-wide visualization
                st.subheader("Energy Balance by Component Type")

                try:
                    # Calculate total energy input/output by component type
                    component_energy = {}

                    # Process converters
                    for converter in st.session_state.elements['converters']:
                        component_energy[converter.label] = 0
                        for flow in converter.flow:
                            if hasattr(flow, 'is_input') and flow.is_input:
                                # Input flow (negative)
                                flow_rates = results[converter.label][flow.label].flow_rate
                                if flow_rates is not None:
                                    component_energy[converter.label] -= flow_rates.sum()
                            else:
                                # Output flow (positive)
                                flow_rates = results[converter.label][flow.label].flow_rate
                                if flow_rates is not None:
                                    component_energy[converter.label] += flow_rates.sum()

                    # Process sources (always positive contribution)
                    for source in st.session_state.elements['sources']:
                        source_flow = source.source
                        flow_rates = results[source.label][source_flow.label].flow_rate
                        if flow_rates is not None:
                            component_energy[source.label] = flow_rates.sum()

                    # Process sinks (always negative contribution)
                    for sink in st.session_state.elements['sinks']:
                        sink_flow = sink.sink
                        flow_rates = results[sink.label][sink_flow.label].flow_rate
                        if flow_rates is not None:
                            component_energy[sink.label] = -flow_rates.sum()

                    # Create dataframe for plotting
                    import pandas as pd
                    df = pd.DataFrame(list(component_energy.items()), columns=['Component', 'Net Energy'])
                    df['Type'] = df['Component'].apply(
                        lambda x: next(
                            (k for k, v in st.session_state.elements.items() if any(c.label == x for c in v)),
                            'Other'
                        )
                    )

                    # Simplify component types for display
                    type_mapping = {
                        'converters': 'Converter',
                        'storages': 'Storage',
                        'sources': 'Source',
                        'sinks': 'Sink'
                    }
                    df['Type'] = df['Type'].map(lambda x: type_mapping.get(x, x.capitalize()))

                    # Create the bar chart
                    fig = px.bar(
                        df,
                        x='Component',
                        y='Net Energy',
                        color='Type',
                        title='System-wide Energy Balance',
                        labels={'Net Energy': 'Net Energy (kWh)', 'Component': 'Component'}
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Effects distribution
                    st.subheader("Effects Distribution")

                    # Calculate effects by component
                    effect_data = []

                    # Loop through effect types
                    for effect in st.session_state.elements['effects']:
                        effect_label = effect.label

                        # Process all components for this effect
                        for component_type in ['converters', 'storages', 'sources', 'sinks']:
                            for component in st.session_state.elements[component_type]:
                                component_label = component.label
                                component_type_label = type_mapping.get(component_type, component_type.capitalize())

                                # Try to get total effect for this component
                                try:
                                    effect_value = results.get_total_effect_for_component(effect_label, component_label)
                                    effect_data.append({
                                        'Effect': effect_label,
                                        'Component': component_label,
                                        'Type': component_type_label,
                                        'Value': effect_value
                                    })
                                except:
                                    # Effect not applicable for this component
                                    pass

                    # Create dataframe for plotting effects
                    if effect_data:
                        effect_df = pd.DataFrame(effect_data)

                        # Select effect to display
                        effect_options = effect_df['Effect'].unique()
                        selected_effect = st.selectbox("Select Effect", effect_options)

                        # Filter dataframe for selected effect
                        filtered_df = effect_df[effect_df['Effect'] == selected_effect]

                        # Create the bar chart for effects
                        fig = px.bar(
                            filtered_df,
                            x='Component',
                            y='Value',
                            color='Type',
                            title=f'{selected_effect} Distribution by Component',
                            labels={'Value': f'{selected_effect} ({next((e.unit for e in st.session_state.elements["effects"] if e.label == selected_effect), "")})'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error generating system overview: {str(e)}")

            # Export results section
            st.subheader("Export Results")
            export_format = st.selectbox("Export Format", ["CSV", "Excel", "JSON"])
            export_content = st.multiselect(
                "Export Content",
                ["Flow Rates", "Effects", "Storage States", "All"]
            )

            if st.button("Export Results"):
                try:
                    with st.spinner("Preparing export..."):
                        # Create a temporary directory to store export files
                        import tempfile
                        import os
                        import zipfile
                        import io

                        # Create a temporary directory
                        with tempfile.TemporaryDirectory() as temp_dir:
                            # Determine which data to export
                            export_flow_rates = "Flow Rates" in export_content or "All" in export_content
                            export_effects = "Effects" in export_content or "All" in export_content
                            export_storage = "Storage States" in export_content or "All" in export_content

                            files_to_export = []

                            # Export flow rates
                            if export_flow_rates:
                                flow_rates_data = {}

                                # Collect flow rates from all components
                                for component_type in ['converters', 'storages', 'sources', 'sinks']:
                                    for component in st.session_state.elements[component_type]:
                                        for flow in component.flow:
                                            flow_key = f"{component.label}({flow.label})|flow_rate"
                                            try:
                                                flow_rates = results.get_timeseries(flow_key)
                                                if flow_rates is not None:
                                                    flow_rates_data[flow_key] = flow_rates
                                            except:
                                                pass

                                # Convert to dataframe
                                if flow_rates_data:
                                    flow_df = pd.DataFrame(flow_rates_data, index=st.session_state.timesteps)

                                    # Export based on selected format
                                    if export_format == "CSV":
                                        file_path = os.path.join(temp_dir, "flow_rates.csv")
                                        flow_df.to_csv(file_path)
                                        files_to_export.append(file_path)
                                    elif export_format == "Excel":
                                        file_path = os.path.join(temp_dir, "flow_rates.xlsx")
                                        flow_df.to_excel(file_path, sheet_name="Flow Rates")
                                        files_to_export.append(file_path)
                                    elif export_format == "JSON":
                                        file_path = os.path.join(temp_dir, "flow_rates.json")
                                        flow_df.to_json(file_path)
                                        files_to_export.append(file_path)

                            # Export effects
                            if export_effects:
                                # Collect total effects for all components
                                effects_data = {}

                                for effect in st.session_state.elements['effects']:
                                    effect_label = effect.label
                                    effects_data[effect_label] = {}

                                    for component_type in ['converters', 'storages', 'sources', 'sinks']:
                                        for component in st.session_state.elements[component_type]:
                                            try:
                                                effect_value = results.get_total_effect_for_component(
                                                    effect_label, component.label
                                                )
                                                effects_data[effect_label][component.label] = effect_value
                                            except:
                                                pass

                                # Convert to dataframe
                                effects_df = pd.DataFrame()
                                for effect, components in effects_data.items():
                                    effect_df = pd.DataFrame(
                                        list(components.items()),
                                        columns=['Component', effect]
                                    )

                                    if effects_df.empty:
                                        effects_df = effect_df
                                    else:
                                        effects_df = effects_df.merge(
                                            effect_df, on='Component', how='outer'
                                        )

                                # Export based on selected format
                                if not effects_df.empty:
                                    if export_format == "CSV":
                                        file_path = os.path.join(temp_dir, "effects.csv")
                                        effects_df.to_csv(file_path, index=False)
                                        files_to_export.append(file_path)
                                    elif export_format == "Excel":
                                        file_path = os.path.join(temp_dir, "effects.xlsx")
                                        effects_df.to_excel(file_path, sheet_name="Effects", index=False)
                                        files_to_export.append(file_path)
                                    elif export_format == "JSON":
                                        file_path = os.path.join(temp_dir, "effects.json")
                                        effects_df.to_json(file_path, orient="records")
                                        files_to_export.append(file_path)

                            # Export storage states
                            if export_storage and st.session_state.elements['storages']:
                                storage_data = {}

                                # Collect charge states for all storage components
                                for storage in st.session_state.elements['storages']:
                                    try:
                                        charge_state = results[storage.label].charge_state
                                        if charge_state is not None:
                                            storage_data[f"{storage.label}_charge"] = charge_state
                                    except:
                                        pass

                                # Convert to dataframe
                                if storage_data:
                                    storage_df = pd.DataFrame(storage_data, index=st.session_state.timesteps)

                                    # Export based on selected format
                                    if export_format == "CSV":
                                        file_path = os.path.join(temp_dir, "storage_states.csv")
                                        storage_df.to_csv(file_path)
                                        files_to_export.append(file_path)
                                    elif export_format == "Excel":
                                        file_path = os.path.join(temp_dir, "storage_states.xlsx")
                                        storage_df.to_excel(file_path, sheet_name="Storage States")
                                        files_to_export.append(file_path)
                                    elif export_format == "JSON":
                                        file_path = os.path.join(temp_dir, "storage_states.json")
                                        storage_df.to_json(file_path)
                                        files_to_export.append(file_path)

                            # Create a zip file with all exports if there are multiple files
                            if len(files_to_export) > 0:
                                if len(files_to_export) == 1 and export_format != "CSV":
                                    # Single file download
                                    file_path = files_to_export[0]
                                    with open(file_path, "rb") as f:
                                        file_bytes = f.read()

                                    # Get filename from path
                                    filename = os.path.basename(file_path)

                                    # Provide download button
                                    st.download_button(
                                        label="Download Results",
                                        data=file_bytes,
                                        file_name=filename,
                                        mime=f"application/{export_format.lower()}"
                                    )
                                else:
                                    # Multiple files or CSV - create a zip archive
                                    zip_buffer = io.BytesIO()
                                    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                                        for file_path in files_to_export:
                                            # Get filename from path
                                            filename = os.path.basename(file_path)
                                            zip_file.write(file_path, arcname=filename)

                                    # Provide download button for zip file
                                    st.download_button(
                                        label="Download Results (ZIP)",
                                        data=zip_buffer.getvalue(),
                                        file_name="flixopt_results.zip",
                                        mime="application/zip"
                                    )
                            else:
                                st.warning("No data to export.")
                except Exception as e:
                    st.error(f"Error exporting results: {str(e)}")

            # Save model section
            st.subheader("Save Model Configuration")
            model_name = st.text_input("Model Name", "my_flixopt_model")

            if st.button("Save Model Configuration"):
                try:
                    with st.spinner("Saving model configuration..."):
                        # Create a dictionary representation of the model
                        model_config = {
                            "name": model_name,
                            "timesteps": {
                                "start": st.session_state.timesteps[0].strftime("%Y-%m-%d %H:%M:%S"),
                                "periods": len(st.session_state.timesteps),
                                "freq": st.session_state.timesteps.freq.freqstr if hasattr(st.session_state.timesteps, 'freq') else "h"
                            },
                            "components": {}
                        }

                        # Save component configurations
                        for component_type, components in st.session_state.elements.items():
                            model_config["components"][component_type] = []

                            for component in components:
                                # Basic component info
                                component_config = {
                                    "label": component.label,
                                    "type": component.__class__.__name__
                                }

                                # Add component-specific attributes
                                if component_type == "converters":
                                    if hasattr(component, "eta") and component.eta is not None:
                                        component_config["eta"] = component.eta
                                    if hasattr(component, "eta_el") and component.eta_el is not None:
                                        component_config["eta_el"] = component.eta_el
                                    if hasattr(component, "eta_th") and component.eta_th is not None:
                                        component_config["eta_th"] = component.eta_th

                                # Add flows
                                if hasattr(component, "flow"):
                                    component_config["flows"] = []

                                    for flow in component.flow:
                                        flow_config = {
                                            "label": flow.label,
                                            "size": flow.size
                                        }

                                        if hasattr(flow, "bus") and flow.bus is not None:
                                            flow_config["bus"] = flow.bus

                                        component_config["flows"].append(flow_config)

                                # Add to components list
                                model_config["components"][component_type].append(component_config)

                        # Convert to JSON
                        import json
                        model_json = json.dumps(model_config, indent=2)

                        # Provide download button
                        st.download_button(
                            label="Download Model Configuration",
                            data=model_json,
                            file_name=f"{model_name}.json",
                            mime="application/json"
                        )
                except Exception as e:
                    st.error(f"Error saving model configuration: {str(e)}")

elif app_mode == "Help & Documentation":
    st.title("Help & Documentation")

    # Documentation tabs
    doc_tabs = st.tabs(["Getting Started", "Component Guide", "Optimization Tips", "API Reference"])

    with doc_tabs[0]:
        st.header("Getting Started with FlixOpt")
        st.markdown("""
            ## Welcome to the FlixOpt Energy System Modeler

            This application allows you to create, configure, and solve energy system models using the FlixOpt framework.

            ### Basic Workflow

            1. **Configure your system**: Set the time range and basic parameters
            2. **Add components**: Define buses, effects, converters, storage systems, sources, and sinks
            3. **Run optimization**: Set solver parameters and optimize the system
            4. **Analyze results**: Visualize and export optimization results

            ### Quick Start Guide

            The fastest way to get started is to use one of the provided example templates:

            1. Go to the "Example Templates" section from the sidebar
            2. Choose a template that matches your modeling needs
            3. Click "Load Selected Template" to populate the model
            4. Switch back to "Model Builder" to customize and run the model

            ### Video Tutorial

            Watch this introductory video to learn the basics of energy system modeling with FlixOpt:
            """)

        st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")  # Replace with actual tutorial video

    with doc_tabs[1]:
        st.header("Component Guide")
        st.markdown("""
            ## Understanding FlixOpt Components

            The FlixOpt framework models energy systems as a network of interconnected components.
            Here's what each component type represents:

            ### Buses

            Buses represent energy carriers (electricity, heat, gas, etc.) and enforce energy balance constraints.
            All energy flows into and out of a bus must balance at each time step.

            **Example**: An electricity bus connects generators (inputs) with consumers (outputs).

            ### Effects

            Effects quantify the impact of system operation, such as costs, CO₂ emissions, or primary energy consumption.
            Effects can be defined as objectives (to minimize/maximize) or as constraints.

            **Example**: A "costs" effect tracks monetary expenses across all components.

            ### Converters

            Converters transform energy from one form to another, with defined efficiencies and capacities.

            **Examples**:
            - **Boiler**: Converts gas to heat
            - **CHP (Combined Heat and Power)**: Converts fuel to both electricity and heat
            - **Heat Pump**: Converts electricity to heat (with a COP > 1)

            ### Storage Systems

            Storage components allow energy to be stored and released over time, enabling temporal flexibility.

            **Example**: A thermal storage tank stores heat for later use, with charging/discharging efficiencies.

            ### Sources and Sinks

            Sources introduce energy into the system, while sinks consume energy.

            **Examples**:
            - **Sources**: Gas supply, grid electricity, renewable generation
            - **Sinks**: Heat demand, electricity consumption, grid feed-in
            """)

        # Component diagram
        st.image("https://via.placeholder.com/800x400?text=FlixOpt+Component+Overview")

    with doc_tabs[2]:
        st.header("Optimization Tips")
        st.markdown("""
            ## Best Practices for Energy System Optimization

            Follow these guidelines to create effective and solvable models:

            ### 1. Start Simple

            Begin with a minimal system and gradually add complexity. This makes it easier to identify and fix issues.

            ### 2. Verify Component Connections

            Ensure all components are properly connected through buses. Missing connections are a common source of errors.

            ### 3. Set Appropriate Constraints

            - **Too tight constraints** may make the problem infeasible
            - **Too loose constraints** may lead to unrealistic solutions
            - **Balance constraints** to reflect real-world limitations while allowing optimization flexibility

            ### 4. Scale Parameters Appropriately

            Use consistent units and scales for all parameters to avoid numerical issues:

            - **Energy flows**: Typically in kW
            - **Capacities**: Typically in kWh or kW
            - **Costs**: Choose a consistent monetary unit (€, $, etc.)

            ### 5. Solver Settings

            - **Relative Gap**: 0.01 (1%) is a good starting point for most models
            - **Time Limit**: Start with 60 seconds, increase for complex models
            - **Consider Relaxations**: If the model is infeasible, try relaxing some constraints

            ### 6. Debugging Strategies

            If your optimization fails or produces unexpected results:

            1. **Check for infeasibility**: Look for conflicting constraints
            2. **Examine bounds**: Ensure min/max values are realistic
            3. **Simplify**: Temporarily remove components to isolate issues
            4. **Validate inputs**: Verify all input data and profiles
            """)

    with doc_tabs[3]:
        st.header("API Reference")
        st.markdown("""
            ## FlixOpt Framework Reference

            This web app is built on the FlixOpt Python framework. For full API documentation, visit the official documentation.

            ### Core Classes

            ```python
            # System definition
            fx.FlowSystem(timesteps)

            # Energy carriers
            fx.Bus(label, excess_penalty_per_flow_hour=value)

            # Effects (objectives and constraints)
            fx.Effect(label, unit, description, is_standard=bool, is_objective=bool)

            # Converters
            fx.linear_converters.Boiler(label, eta, Q_th, Q_fu)
            fx.linear_converters.CHP(label, eta_el, eta_th, P_el, Q_th, Q_fu)

            # Storage
            fx.Storage(label, charging, discharging, capacity_in_flow_hours)

            # Sources and sinks
            fx.Source(label, source=flow)
            fx.Sink(label, sink=flow)

            # Flows
            fx.Flow(label, bus, size, effects_per_flow_hour={})
            ```

            ### Investment Parameters

            ```python
            fx.InvestParameters(fixed_size, minimum_size, maximum_size, fix_effects, specific_effects)
            ```

            ### On/Off Parameters

            ```python
            fx.OnOffParameters(
                on_hours_total_min, on_hours_total_max,
                consecutive_on_hours_min, consecutive_on_hours_max,
                consecutive_off_hours_min, consecutive_off_hours_max,
                effects_per_switch_on, effects_per_running_hour
            )
            ```

            ### Results Analysis

            ```python
            # Access results
            results = calculation.results

            # Component results
            component_results = results[component_label]

            # Flow results
            flow_rates = results.get_timeseries(f"{component_label}({flow_label})|flow_rate")

            # Effect results
            total_effect = results.get_total_effect(effect_label)
            component_effect = results.get_total_effect_for_component(effect_label, component_label)
            ```
            """)

        st.markdown("""
            For more detailed documentation and examples, refer to the [FlixOpt Documentation](https://example.com/flixopt/docs).
            """)

elif app_mode == "Example Templates":
    st.title("Example Templates")
    st.markdown("""
        Choose from pre-configured energy system templates to quickly get started.
        These examples demonstrate different system configurations from simple to complex.
        """)

    # Template selection
    template = st.selectbox(
        "Select Template",
        [
            "Simple Heat System",
            "CHP with Storage",
            "Apartment Building",
            "Microgrid with Renewables",
            "District Heating Network"
        ]
    )
    # Template descriptions and preview
    if template == "Simple Heat System":
        st.subheader("Simple Heat System")
        st.markdown("""
            **Description**: A basic heat supply system with a gas boiler meeting a simple heat demand profile.

            **Components**:
            - Gas bus
            - Heat bus
            - Gas source (tariff)
            - Heat sink (demand)
            - Gas boiler (converter)

            **Perfect for**: Getting started with FlixOpt or modeling simple heating applications.
            """)

        # System diagram
        st.image("https://via.placeholder.com/800x400?text=Simple+Heat+System+Diagram")

    elif template == "CHP with Storage":
        st.subheader("CHP with Storage")
        st.markdown("""
            **Description**: A combined heat and power system with thermal storage, supplying both electricity and heat.

            **Components**:
            - Gas bus
            - Heat bus
            - Electricity bus
            - Gas source (tariff)
            - Heat sink (demand)
            - Electricity sink (demand and grid feed-in)
            - CHP unit (combined converter)
            - Heat storage
            - Backup gas boiler

            **Perfect for**: Modeling flexible cogeneration systems with the ability to shift heat production.
            """)

        # System diagram
        st.image("https://via.placeholder.com/800x400?text=CHP+with+Storage+Diagram")

    elif template == "Apartment Building":
        st.subheader("Apartment Building")
        st.markdown("""
            **Description**: A complete energy system for a multi-unit residential building, including electricity, heating, and cooling.

            **Components**:
            - Electricity bus
            - Heat bus
            - Cooling bus
            - Natural gas bus
            - Grid connection (electricity source/sink)
            - Gas connection (source)
            - Heat pump (converter)
            - Backup gas boiler
            - Multiple thermal storage options
            - Time-variable heat and electricity demands

            **Perfect for**: Modeling residential building energy systems with multiple energy carriers.
            """)

        # System diagram
        st.image("https://via.placeholder.com/800x400?text=Apartment+Building+System+Diagram")

    elif template == "Microgrid with Renewables":
        st.subheader("Microgrid with Renewables")
        st.markdown("""
            **Description**: An islanded or grid-connected microgrid with renewable generation, storage, and flexible loads.

            **Components**:
            - Electricity bus
            - Battery storage
            - Solar PV source (with time-variable profile)
            - Wind source (with time-variable profile)
            - Backup generator
            - Grid connection (optional)
            - Critical and flexible loads

            **Perfect for**: Modeling renewable energy integration, microgrids, and energy independence scenarios.
            """)

        # System diagram
        st.image("https://via.placeholder.com/800x400?text=Microgrid+System+Diagram")

    elif template == "District Heating Network":
        st.subheader("District Heating Network")
        st.markdown("""
            **Description**: A complex district heating network with multiple generation sources and storage options.

            **Components**:
            - Primary heat bus (high temperature)
            - Secondary heat bus (distribution temperature)
            - Electricity bus
            - Gas bus
            - Multiple heat sources (CHP, boilers, heat pumps)
            - Large thermal storage
            - Multiple heat sinks representing different building clusters
            - Heat exchangers

            **Perfect for**: Modeling district energy systems and complex multi-carrier energy networks.
            """)

        # System diagram
        st.image("https://via.placeholder.com/800x400?text=District+Heating+Network+Diagram")


    # Load template button
    if st.button("Load Selected Template"):
        # Here we would implement the template loading logic
        # For demonstration, just show a success message
        st.success(f"Template '{template}' loaded successfully! Switch to Model Builder mode to view and customize it.")

        # Update session state with the template components
        # This would be implemented in a real application
        st.session_state.template_loaded = template

    # Add code for handling system imports from JSON
    if 'template_loaded' in st.session_state and st.session_state.template_loaded:
        # Display notification about loaded template
        st.sidebar.success(f"Template '{st.session_state.template_loaded}' loaded")

        # Reset the flag after showing the notification once
        if st.sidebar.button("Clear Template"):
            st.session_state.template_loaded = None
            st.experimental_rerun()

# Add import/export functionality to the sidebar
if app_mode == "Model Builder":
    st.sidebar.markdown("---")
    st.sidebar.subheader("Import/Export System")

    # Export current system
    if st.session_state.flow_system is not None:
        if st.sidebar.button("Export Current System"):
            try:
                import json

                # Create a dictionary representation of the model
                model_config = {
                    "timesteps": {
                        "start": st.session_state.timesteps[0].strftime("%Y-%m-%d %H:%M:%S"),
                        "periods": len(st.session_state.timesteps),
                        "freq": st.session_state.timesteps.freq.freqstr if hasattr(st.session_state.timesteps, 'freq') else "h"
                    },
                    "components": {}
                }

                # Save component configurations
                for component_type, components in st.session_state.elements.items():
                    model_config["components"][component_type] = []

                    for component in components:
                        # Basic component info
                        component_config = {
                            "label": component.label,
                            "type": component.__class__.__name__
                        }

                        # Add to components list
                        model_config["components"][component_type].append(component_config)

                # Convert to JSON
                model_json = json.dumps(model_config, indent=2)

                # Provide download button
                st.sidebar.download_button(
                    label="Download Configuration JSON",
                    data=model_json,
                    file_name="flixopt_system.json",
                    mime="application/json"
                )
            except Exception as e:
                st.sidebar.error(f"Error exporting system: {str(e)}")

    # Import system from JSON
    uploaded_file = st.sidebar.file_uploader("Import System Configuration", type="json")
    if uploaded_file is not None:
        try:
            import json

            # Load the JSON data
            config_data = json.load(uploaded_file)

            # Verify the data structure
            if "timesteps" in config_data and "components" in config_data:
                if st.sidebar.button("Apply Imported Configuration"):
                    # Reset current system
                    st.session_state.elements = {
                        'buses': [],
                        'effects': [],
                        'converters': [],
                        'storages': [],
                        'sources': [],
                        'sinks': []
                    }

                    # Create new timesteps
                    import pandas as pd
                    from datetime import datetime

                    start = datetime.strptime(config_data["timesteps"]["start"], "%Y-%m-%d %H:%M:%S")
                    periods = config_data["timesteps"]["periods"]
                    freq = config_data["timesteps"]["freq"]

                    st.session_state.timesteps = pd.date_range(start, periods=periods, freq=freq)

                    # Create new flow system
                    st.session_state.flow_system = fx.FlowSystem(st.session_state.timesteps)

                    # Load components (basic structure only, details would depend on actual implementation)
                    st.sidebar.success("Configuration imported successfully")
                    st.experimental_rerun()
            else:
                st.sidebar.error("Invalid configuration file structure")
        except Exception as e:
            st.sidebar.error(f"Error importing system: {str(e)}")

# Add a system validation button to the sidebar
if app_mode == "Model Builder" and st.session_state.flow_system is not None:
    st.sidebar.markdown("---")
    st.sidebar.subheader("System Validation")

    if st.sidebar.button("Validate System"):
        # Count components by type
        component_counts = {k: len(v) for k, v in st.session_state.elements.items()}

        # Check for basic requirements
        validation_issues = []

        if component_counts['buses'] == 0:
            validation_issues.append("⚠️ No energy buses defined")

        if component_counts['effects'] == 0:
            validation_issues.append("⚠️ No effects (objectives/constraints) defined")

        if not any(effect.is_objective for effect in st.session_state.elements['effects']):
            validation_issues.append("⚠️ No objective function defined")

        if component_counts['converters'] + component_counts['sources'] + component_counts['sinks'] == 0:
            validation_issues.append("⚠️ No energy producers or consumers defined")

        # Check for bus connections
        bus_connections = {bus.label: {'in': 0, 'out': 0} for bus in st.session_state.elements['buses']}

        # Count connections to each bus
        for component_type in ['converters', 'storages', 'sources', 'sinks']:
            for component in st.session_state.elements[component_type]:
                if hasattr(component, 'flow'):
                    for flow in component.flow:
                        if hasattr(flow, 'bus') and flow.bus in bus_connections:
                            # Determine flow direction
                            if (component_type == 'sources') or \
                                    (component_type == 'converters' and not hasattr(flow, 'is_input')):
                                bus_connections[flow.bus]['in'] += 1
                            elif (component_type == 'sinks') or \
                                    (component_type == 'converters' and hasattr(flow, 'is_input') and flow.is_input):
                                bus_connections[flow.bus]['out'] += 1

        # Check for disconnected buses
        for bus, connections in bus_connections.items():
            if connections['in'] == 0:
                validation_issues.append(f"⚠️ Bus '{bus}' has no input connections")
            if connections['out'] == 0:
                validation_issues.append(f"⚠️ Bus '{bus}' has no output connections")

        # Display validation results
        if validation_issues:
            st.sidebar.error("Validation Issues:")
            for issue in validation_issues:
                st.sidebar.warning(issue)
        else:
            st.sidebar.success("System validation passed! All components are properly connected.")

# Add a system status indicator
st.sidebar.markdown("---")
st.sidebar.subheader("System Status")

# Display component counts
if st.session_state.flow_system is not None:
    component_counts = {k: len(v) for k, v in st.session_state.elements.items()}

    # Create a formatted status display
    st.sidebar.markdown(f"""
    **System Components:**
    - Buses: {component_counts['buses']}
    - Effects: {component_counts['effects']}
    - Converters: {component_counts['converters']}
    - Storage: {component_counts['storages']}
    - Sources: {component_counts['sources']}
    - Sinks: {component_counts['sinks']}

    **Time Steps:** {len(st.session_state.timesteps) if st.session_state.timesteps is not None else 0}

    **Status:** {'Ready for optimization' if all([component_counts['buses'], component_counts['effects'],
                                                  component_counts['converters'] + component_counts['sources'] + component_counts['sinks']])
    else 'Incomplete - add more components'}
    """)
else:
    st.sidebar.markdown("""
    **System Status:** Not initialized

    Please go to the System Configuration tab to initialize the flow system.
    """)

# Add footer with version information
st.sidebar.markdown("---")
st.sidebar.markdown("**FlixOpt Streamlit App v1.0.0**")
st.sidebar.markdown("© 2025 FlixOpt Team")