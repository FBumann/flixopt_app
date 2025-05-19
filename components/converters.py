import streamlit as st
import flixopt as fx
from utils.session_state import add_element, delete_element

def create_converter_ui():
    """UI for creating and managing converters"""
    st.subheader("Converters")
    st.write("Converters transform energy from one form to another, like boilers or CHP units.")

    # If no buses exist, inform the user
    if not st.session_state.elements['buses']:
        st.warning("Please create at least one bus before adding converters.")
        return

    converter_type = st.selectbox(
        "Converter Type",
        ["Boiler", "CHP (Combined Heat and Power)", "Heat Pump"]
    )

    if converter_type == "Boiler":
        create_boiler_ui()
    elif converter_type == "CHP (Combined Heat and Power)":
        create_chp_ui()
    elif converter_type == "Heat Pump":
        create_heat_pump_ui()

    # Display existing converters
    display_existing_converters()

def create_boiler_ui():
    """UI for creating a boiler converter"""
    with st.form("boiler_form"):
        boiler_name = st.text_input("Boiler Name", value="Kessel")
        boiler_eta = st.slider("Efficiency (η)", min_value=0.5, max_value=1.0, value=0.85, step=0.01)

        st.subheader("Thermal Output (Q_th)")
        q_th_bus = st.selectbox("Output Bus", list(st.session_state.flow_system.buses), key="q_th_bus")
        q_th_size = st.number_input("Size (kW)", min_value=0.001, value=50.0, key="q_th_size")
        q_th_min_load = st.slider("Minimum Load Factor", min_value=0.0, max_value=1.0, value=0.1, step=0.01)

        st.subheader("Fuel Input (Q_fu)")
        q_fu_bus = st.selectbox("Input Bus", list(st.session_state.flow_system.buses), key="q_fu_bus")

        col1, col2 = st.columns(2)
        with col1:
            on_off_params = st.checkbox("Add On/Off Parameters", value=False)
        with col2:
            investment_params = st.checkbox("Add Investment Parameters", value=False)

        # On/Off Parameters (if selected)
        if on_off_params:
            st.subheader("On/Off Parameters")
            add_on_off_parameters_ui("boiler")

        # Investment Parameters (if selected)
        if investment_params:
            st.subheader("Investment Parameters")
            add_investment_parameters_ui("boiler")

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

                success, message = add_element(boiler, 'converters')

                if success:
                    st.success(message)
                else:
                    st.error(message)
            except Exception as e:
                st.error(f"Error adding boiler: {str(e)}")

def create_chp_ui():
    """UI for creating a CHP converter"""
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

        col1, col2 = st.columns(2)
        with col1:
            on_off_params = st.checkbox("Add On/Off Parameters", value=False, key="chp_on_off")
        with col2:
            investment_params = st.checkbox("Add Investment Parameters", value=False, key="chp_invest")

        # On/Off Parameters (if selected)
        if on_off_params:
            st.subheader("On/Off Parameters")
            add_on_off_parameters_ui("chp")

        # Investment Parameters (if selected)
        if investment_params:
            st.subheader("Investment Parameters")
            add_investment_parameters_ui("chp")

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

                success, message = add_element(chp, 'converters')

                if success:
                    st.success(message)
                else:
                    st.error(message)
            except Exception as e:
                st.error(f"Error adding CHP: {str(e)}")

def create_heat_pump_ui():
    """UI for creating a heat pump converter"""
    with st.form("heat_pump_form"):
        hp_name = st.text_input("Heat Pump Name", value="Wärmepumpe")
        cop = st.slider("COP (Coefficient of Performance)", min_value=1.0, max_value=6.0, value=3.5, step=0.1)

        st.subheader("Heat Output (Q_out)")
        q_out_bus = st.selectbox("Output Heat Bus", list(st.session_state.flow_system.buses), key="q_out_bus")
        q_out_size = st.number_input("Thermal Size (kW)", min_value=1.0, value=50.0)
        q_out_min_load = st.slider("Minimum Load Factor", min_value=0.0, max_value=1.0, value=0.3, step=0.01)

        st.subheader("Electricity Input (P_el)")
        p_el_bus = st.selectbox("Electricity Bus", list(st.session_state.flow_system.buses), key="hp_p_el_bus")

        col1, col2 = st.columns(2)
        with col1:
            on_off_params = st.checkbox("Add On/Off Parameters", value=False, key="hp_on_off")
        with col2:
            investment_params = st.checkbox("Add Investment Parameters", value=False, key="hp_invest")

        # On/Off Parameters (if selected)
        if on_off_params:
            st.subheader("On/Off Parameters")
            add_on_off_parameters_ui("hp")

        # Investment Parameters (if selected)
        if investment_params:
            st.subheader("Investment Parameters")
            add_investment_parameters_ui("hp")

        if st.form_submit_button("Add Heat Pump"):
            try:
                # Create custom heat pump converter
                p_el_size = q_out_size / cop

                # Create heat pump (using LinearConverter)
                hp = fx.LinearConverter(
                    hp_name,
                    [
                        fx.Flow('Q_out', bus=q_out_bus, size=q_out_size, relative_minimum=q_out_min_load)
                    ],
                    [
                        fx.Flow('P_el', bus=p_el_bus, size=p_el_size)
                    ],
                    [[1/cop]]  # Conversion matrix (1 kW heat output requires 1/COP kW electricity)
                )

                success, message = add_element(hp, 'converters')

                if success:
                    st.success(message)
                else:
                    st.error(message)
            except Exception as e:
                st.error(f"Error adding heat pump: {str(e)}")

def add_on_off_parameters_ui(prefix):
    """Helper function to add on/off parameters UI elements"""
    col1, col2 = st.columns(2)

    with col1:
        on_hours_min = st.number_input(f"Min Total On Hours",
                                       min_value=0,
                                       value=0,
                                       key=f"{prefix}_on_hours_min")
        consecutive_on_min = st.number_input(f"Min Consecutive On Hours",
                                             min_value=0,
                                             value=1,
                                             key=f"{prefix}_consecutive_on_min")
        consecutive_off_min = st.number_input(f"Min Consecutive Off Hours",
                                              min_value=0,
                                              value=1,
                                              key=f"{prefix}_consecutive_off_min")

    with col2:
        on_hours_max = st.number_input(f"Max Total On Hours",
                                       min_value=0,
                                       value=None,
                                       key=f"{prefix}_on_hours_max")
        consecutive_on_max = st.number_input(f"Max Consecutive On Hours",
                                             min_value=0,
                                             value=None,
                                             key=f"{prefix}_consecutive_on_max")
        consecutive_off_max = st.number_input(f"Max Consecutive Off Hours",
                                              min_value=0,
                                              value=None,
                                              key=f"{prefix}_consecutive_off_max")

    # Switch-on costs
    switch_on_effects = {}
    if st.session_state.elements['effects']:
        st.subheader("Switch-On Effects")
        for effect in st.session_state.elements['effects']:
            value = st.number_input(f"{effect.label} per Switch-On",
                                    value=0.0,
                                    key=f"{prefix}_switch_{effect.label}")
            if value != 0:
                switch_on_effects[effect.label] = value

    # Running hour costs
    running_hour_effects = {}
    if st.session_state.elements['effects']:
        st.subheader("Running Hour Effects")
        for effect in st.session_state.elements['effects']:
            value = st.number_input(f"{effect.label} per Running Hour",
                                    value=0.0,
                                    key=f"{prefix}_running_{effect.label}")
            if value != 0:
                running_hour_effects[effect.label] = value

    # Return the parameters dictionary
    return {
        'on_hours_total_min': on_hours_min,
        'on_hours_total_max': on_hours_max,
        'consecutive_on_hours_min': consecutive_on_min,
        'consecutive_on_hours_max': consecutive_on_max,
        'consecutive_off_hours_min': consecutive_off_min,
        'consecutive_off_hours_max': consecutive_off_max,
        'effects_per_switch_on': switch_on_effects,
        'effects_per_running_hour': running_hour_effects
    }

def add_investment_parameters_ui(prefix):
    """Helper function to add investment parameters UI elements"""
    col1, col2 = st.columns(2)

    with col1:
        fixed_size = st.checkbox("Fixed Size", value=False, key=f"{prefix}_fixed_size")
        minimum_size = st.number_input("Minimum Size",
                                       min_value=0.0,
                                       value=0.0,
                                       key=f"{prefix}_min_size")

    with col2:
        maximum_size = st.number_input("Maximum Size",
                                       min_value=0.0,
                                       value=None,
                                       key=f"{prefix}_max_size")

    # Fixed effects
    fixed_effects = {}
    if st.session_state.elements['effects']:
        st.subheader("Fixed Effects")
        for effect in st.session_state.elements['effects']:
            value = st.number_input(f"Fixed {effect.label}",
                                    value=0.0,
                                    key=f"{prefix}_fixed_{effect.label}")
            if value != 0:
                fixed_effects[effect.label] = value

    # Specific effects
    specific_effects = {}
    if st.session_state.elements['effects']:
        st.subheader("Specific Effects (per kW)")
        for effect in st.session_state.elements['effects']:
            value = st.number_input(f"{effect.label} per kW",
                                    value=0.0,
                                    key=f"{prefix}_specific_{effect.label}")
            if value != 0:
                specific_effects[effect.label] = value

    # Return the parameters dictionary
    return {
        'fixed_size': fixed_size,
        'minimum_size': minimum_size,
        'maximum_size': maximum_size,
        'fix_effects': fixed_effects,
        'specific_effects': specific_effects
    }

def display_existing_converters():
    """Display the list of existing converters"""
    if not st.session_state.elements['converters']:
        return

    st.write("Current Converters:")

    # Create a table of converters with options to edit/delete
    cols = st.columns([3, 2, 1])
    cols[0].write("**Name**")
    cols[1].write("**Type**")
    cols[2].write("**Actions**")

    for i, converter in enumerate(st.session_state.flow_system.components.values()):
        cols = st.columns([3, 2, 1])
        cols[0].write(converter.label_full)

        # Determine converter type
        converter_type = type(converter).__name__
        cols[1].write(converter_type)

        # Action buttons
        if cols[2].button("Delete", key=f"delete_converter_{converter.label_full}"):
            delete_element(converter.label_full, 'converters')
            st.rerun()

        # Show details in an expander
        with st.expander(f"Details: {converter.label}"):
            st.write(f"**Type:** {converter_type}")

            # Show flows
            if hasattr(converter, 'flow'):
                st.write("**Flows:**")
                for flow in converter.flow:
                    flow_direction = "Input" if hasattr(flow, 'is_input') and flow.is_input else "Output"
                    st.write(f"- {flow.label}: {flow_direction}, Size: {flow.size} kW, Bus: {flow.bus}")

            # Show efficiencies
            if hasattr(converter, 'eta'):
                st.write(f"**Efficiency:** {converter.eta:.2f}")
            if hasattr(converter, 'eta_el'):
                st.write(f"**Electrical Efficiency:** {converter.eta_el:.2f}")
            if hasattr(converter, 'eta_th'):
                st.write(f"**Thermal Efficiency:** {converter.eta_th:.2f}")
