import streamlit as st
import flixopt as fx
import pandas as pd
import numpy as np
from datetime import datetime
from utils.session_state import reset_system, initialize_flow_system

def render_templates_page():
    """Render the Example Templates page"""
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

    # Show template description and details
    if template == "Simple Heat System":
        render_simple_heat_template()
    elif template == "CHP with Storage":
        render_chp_template()
    elif template == "Apartment Building":
        render_apartment_template()
    elif template == "Microgrid with Renewables":
        render_microgrid_template()
    elif template == "District Heating Network":
        render_district_heating_template()

    # Load template button
    if st.button("Load Selected Template"):
        # Reset current system
        reset_system()

        # Load the selected template
        if template == "Simple Heat System":
            load_simple_heat_template()
        elif template == "CHP with Storage":
            load_chp_template()
        elif template == "Apartment Building":
            load_apartment_template()
        elif template == "Microgrid with Renewables":
            load_microgrid_template()
        elif template == "District Heating Network":
            load_district_heating_template()

        # Update the template loaded flag
        st.session_state.template_loaded = template
        st.success(f"Template '{template}' loaded successfully! Switch to Model Builder mode to view and customize it.")

    # Add code for handling system imports from JSON
    if 'template_loaded' in st.session_state and st.session_state.template_loaded:
        # Display notification about loaded template
        st.sidebar.success(f"Template '{st.session_state.template_loaded}' loaded")

        # Reset the flag after showing the notification once
        if st.sidebar.button("Clear Template"):
            st.session_state.template_loaded = None
            st.rerun()

def render_simple_heat_template():
    """Render the Simple Heat System template description"""
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

def render_chp_template():
    """Render the CHP with Storage template description"""
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

def render_apartment_template():
    """Render the Apartment Building template description"""
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

def render_microgrid_template():
    """Render the Microgrid with Renewables template description"""
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

def render_district_heating_template():
    """Render the District Heating Network template description"""
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

def load_simple_heat_template():
    """Load the Simple Heat System template components"""
    # Initialize system with 24 hour timeframe
    initialize_flow_system(
        start_date=datetime.now().date(),
        periods=24,
        freq="h",
        excess_penalty=1e3
    )

    # Add effects (costs)
    costs = fx.Effect("costs", "€", "Costs", is_standard=True, is_objective=True)
    st.session_state.flow_system.add_elements(costs)
    st.session_state.elements['effects'].append(costs)

    # Add buses
    gas_bus = fx.Bus("Gas", excess_penalty_per_flow_hour=1e3)
    heat_bus = fx.Bus("Heat", excess_penalty_per_flow_hour=1e3)

    st.session_state.flow_system.add_elements(gas_bus)
    st.session_state.flow_system.add_elements(heat_bus)
    st.session_state.elements['buses'].extend([gas_bus, heat_bus])

    # Add gas source
    gas_flow = fx.Flow(
        'gas_flow',
        bus="Gas",
        size=1000,
        effects_per_flow_hour={"costs": 0.06}  # €/kWh
    )
    gas_source = fx.Source("Gas_Source", source=gas_flow)

    st.session_state.flow_system.add_elements(gas_source)
    st.session_state.elements['sources'].append(gas_source)

    # Add boiler
    boiler = fx.linear_converters.Boiler(
        "Boiler",
        eta=0.9,
        Q_th=fx.Flow('Q_th', bus="Heat", size=50, relative_minimum=0.1),
        Q_fu=fx.Flow('Q_fu', bus="Gas", size=55.55)  # Sized for efficiency
    )

    st.session_state.flow_system.add_elements(boiler)
    st.session_state.elements['converters'].append(boiler)

    # Add heat demand with a simple daily profile
    heat_profile = np.ones(24)
    # Simulate higher demand in morning and evening
    heat_profile[5:8] = 1.5  # Morning peak
    heat_profile[17:22] = 1.8  # Evening peak
    heat_profile[0:5] = 0.7  # Night reduction

    heat_flow = fx.Flow(
        'heat_flow',
        bus="Heat",
        size=40,
        fixed_relative_profile=heat_profile
    )
    heat_sink = fx.Sink("Heat_Demand", sink=heat_flow)

    st.session_state.flow_system.add_elements(heat_sink)
    st.session_state.elements['sinks'].append(heat_sink)

def load_chp_template():
    """Load the CHP with Storage template components"""
    # Initialize system with 48 hour timeframe for better storage visibility
    initialize_flow_system(
        start_date=datetime.now().date(),
        periods=48,
        freq="h",
        excess_penalty=1e3
    )

    # Add effects (costs and CO2 emissions)
    costs = fx.Effect("costs", "€", "Costs", is_standard=True, is_objective=True)
    emissions = fx.Effect("CO2", "kg", "CO2 Emissions", is_standard=True, is_objective=False, maximum_total=1000)

    st.session_state.flow_system.add_elements(costs)
    st.session_state.flow_system.add_elements(emissions)
    st.session_state.elements['effects'].extend([costs, emissions])

    # Add buses
    gas_bus = fx.Bus("Gas", excess_penalty_per_flow_hour=1e3)
    heat_bus = fx.Bus("Heat", excess_penalty_per_flow_hour=1e3)
    elec_bus = fx.Bus("Electricity", excess_penalty_per_flow_hour=1e3)

    st.session_state.flow_system.add_elements(gas_bus)
    st.session_state.flow_system.add_elements(heat_bus)
    st.session_state.flow_system.add_elements(elec_bus)
    st.session_state.elements['buses'].extend([gas_bus, heat_bus, elec_bus])

    # Add gas source
    gas_flow = fx.Flow(
        'gas_flow',
        bus="Gas",
        size=1000,
        effects_per_flow_hour={"costs": 0.06, "CO2": 0.2}  # €/kWh, kg/kWh
    )
    gas_source = fx.Source("Gas_Source", source=gas_flow)

    st.session_state.flow_system.add_elements(gas_source)
    st.session_state.elements['sources'].append(gas_source)

    # Add grid source & sink (for buying and selling electricity)
    grid_in_flow = fx.Flow(
        'grid_in_flow',
        bus="Electricity",
        size=1000,
        effects_per_flow_hour={"costs": 0.30, "CO2": 0.4}  # €/kWh, kg/kWh
    )
    grid_in = fx.Source("Grid_Import", source=grid_in_flow)

    grid_out_flow = fx.Flow(
        'grid_out_flow',
        bus="Electricity",
        size=1000,
        effects_per_flow_hour={"costs": -0.15}  # Negative cost (revenue)
    )
    grid_out = fx.Sink("Grid_Export", sink=grid_out_flow)

    st.session_state.flow_system.add_elements(grid_in)
    st.session_state.flow_system.add_elements(grid_out)
    st.session_state.elements['sources'].append(grid_in)
    st.session_state.elements['sinks'].append(grid_out)

    # Add CHP unit
    chp = fx.linear_converters.CHP(
        "CHP_Unit",
        eta_el=0.35,
        eta_th=0.5,
        P_el=fx.Flow('P_el', bus="Electricity", size=40, relative_minimum=0.4),
        Q_th=fx.Flow('Q_th', bus="Heat", size=57.14),  # Sized for efficiency ratio
        Q_fu=fx.Flow('Q_fu', bus="Gas", size=114.29)   # Sized for efficiency
    )

    st.session_state.flow_system.add_elements(chp)
    st.session_state.elements['converters'].append(chp)

    # Add backup boiler
    boiler = fx.linear_converters.Boiler(
        "Backup_Boiler",
        eta=0.9,
        Q_th=fx.Flow('Q_th', bus="Heat", size=100, relative_minimum=0.1),
        Q_fu=fx.Flow('Q_fu', bus="Gas", size=111.11)  # Sized for efficiency
    )

    st.session_state.flow_system.add_elements(boiler)
    st.session_state.elements['converters'].append(boiler)

    # Add heat storage
    storage = fx.Storage(
        "Heat_Storage",
        charging=fx.Flow('charging', bus="Heat", size=50),
        discharging=fx.Flow('discharging', bus="Heat", size=50),
        capacity_in_flow_hours=4,  # 200 kWh
        initial_charge_state=0,
        eta_charge=0.95,
        eta_discharge=0.95,
        relative_loss_per_hour=0.01,
        prevent_simultaneous_charge_and_discharge=True
    )

    st.session_state.flow_system.add_elements(storage)
    st.session_state.elements['storages'].append(storage)

    # Add heat demand with a simple daily profile (repeated for 2 days)
    heat_profile_day = np.ones(24)
    # Simulate higher demand in morning and evening
    heat_profile_day[5:8] = 1.5  # Morning peak
    heat_profile_day[17:22] = 1.8  # Evening peak
    heat_profile_day[0:5] = 0.7  # Night reduction

    # Repeat for 2 days
    heat_profile = np.tile(heat_profile_day, 2)

    heat_flow = fx.Flow(
        'heat_flow',
        bus="Heat",
        size=50,
        fixed_relative_profile=heat_profile
    )
    heat_sink = fx.Sink("Heat_Demand", sink=heat_flow)

    st.session_state.flow_system.add_elements(heat_sink)
    st.session_state.elements['sinks'].append(heat_sink)

    # Add electricity demand with a daily profile (repeated for 2 days)
    elec_profile_day = np.ones(24)
    # Simulate higher demand in morning and evening
    elec_profile_day[7:9] = 1.4  # Morning peak
    elec_profile_day[18:23] = 1.6  # Evening peak
    elec_profile_day[0:7] = 0.6  # Night reduction

    # Repeat for 2 days
    elec_profile = np.tile(elec_profile_day, 2)

    elec_flow = fx.Flow(
        'elec_flow',
        bus="Electricity",
        size=30,
        fixed_relative_profile=elec_profile
    )
    elec_sink = fx.Sink("Electricity_Demand", sink=elec_flow)

    st.session_state.flow_system.add_elements(elec_sink)
    st.session_state.elements['sinks'].append(elec_sink)

def load_apartment_template():
    """Load the Apartment Building template components"""
    # This is a placeholder implementation that would be expanded in a real application
    initialize_flow_system(
        start_date=datetime.now().date(),
        periods=24,
        freq="h",
        excess_penalty=1e3
    )

    # Add a basic effect
    costs = fx.Effect("costs", "€", "Costs", is_standard=True, is_objective=True)
    st.session_state.flow_system.add_elements(costs)
    st.session_state.elements['effects'].append(costs)

    # Add basic buses
    elec_bus = fx.Bus("Electricity", excess_penalty_per_flow_hour=1e3)
    heat_bus = fx.Bus("Heat", excess_penalty_per_flow_hour=1e3)
    gas_bus = fx.Bus("Gas", excess_penalty_per_flow_hour=1e3)

    st.session_state.flow_system.add_elements(elec_bus)
    st.session_state.flow_system.add_elements(heat_bus)
    st.session_state.flow_system.add_elements(gas_bus)
    st.session_state.elements['buses'].extend([elec_bus, heat_bus, gas_bus])

    # Basic placeholder message
    st.warning("The Apartment Building template is simplified in this demo. In a complete implementation, it would include more detailed components and load profiles.")

def load_microgrid_template():
    """Load the Microgrid with Renewables template components"""
    # This is a placeholder implementation that would be expanded in a real application
    initialize_flow_system(
        start_date=datetime.now().date(),
        periods=24,
        freq="h",
        excess_penalty=1e3
    )

    # Add a basic effect
    costs = fx.Effect("costs", "€", "Costs", is_standard=True, is_objective=True)
    st.session_state.flow_system.add_elements(costs)
    st.session_state.elements['effects'].append(costs)

    # Add basic bus
    elec_bus = fx.Bus("Electricity", excess_penalty_per_flow_hour=1e3)
    st.session_state.flow_system.add_elements(elec_bus)
    st.session_state.elements['buses'].append(elec_bus)

    # Basic placeholder message
    st.warning("The Microgrid template is simplified in this demo. In a complete implementation, it would include solar PV, wind generation, battery storage, and detailed load profiles.")

def load_district_heating_template():
    """Load the District Heating Network template components"""
    # This is a placeholder implementation that would be expanded in a real application
    initialize_flow_system(
        start_date=datetime.now().date(),
        periods=24,
        freq="h",
        excess_penalty=1e3
    )

    # Add a basic effect
    costs = fx.Effect("costs", "€", "Costs", is_standard=True, is_objective=True)
    st.session_state.flow_system.add_elements(costs)
    st.session_state.elements['effects'].append(costs)

    # Add basic buses
    primary_heat_bus = fx.Bus("Primary_Heat", excess_penalty_per_flow_hour=1e3)
    secondary_heat_bus = fx.Bus("Secondary_Heat", excess_penalty_per_flow_hour=1e3)

    st.session_state.flow_system.add_elements(primary_heat_bus)
    st.session_state.flow_system.add_elements(secondary_heat_bus)
    st.session_state.elements['buses'].extend([primary_heat_bus, secondary_heat_bus])

    # Basic placeholder message
    st.warning("The District Heating Network template is simplified in this demo. In a complete implementation, it would include multiple heat sources, district-level storage, and building clusters.")
