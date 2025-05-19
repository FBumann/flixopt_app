import streamlit as st
import flixopt as fx
from utils.session_state import add_element, delete_element

def create_bus_ui():
    """UI for creating and managing buses"""
    st.subheader("Energy Buses")
    st.write("Buses represent node balances (inputs=outputs) for different energy carriers in the system.")

    # Get default excess penalty if available
    default_excess_penalty = None
    if 'default_excess_penalty' in st.session_state:
        default_excess_penalty = st.session_state.default_excess_penalty

    with st.form("bus_form"):
        bus_name = st.text_input("Bus Name", value="Bus")
        bus_excess_penalty = st.number_input(
            "Excess Penalty per Flow Hour",
            min_value=0.0,
            value=default_excess_penalty if default_excess_penalty is not None else 1e3,
            format="%.1e"
        )

        if st.form_submit_button("Add Bus"):
            if st.session_state.flow_system is None:
                st.error("Please initialize the flow system first.")
                return

            new_bus = fx.Bus(
                bus_name,
                excess_penalty_per_flow_hour=bus_excess_penalty
            )
            success, message = add_element(new_bus, 'buses')

            if success:
                st.success(message)
            else:
                st.error(message)

    # Display existing buses
    display_existing_buses()

def display_existing_buses():
    """Display the list of existing buses"""
    if not st.session_state.elements['buses']:
        return

    st.write("Current Buses:")

    # Create a table of buses with options to edit/delete
    cols = st.columns([3, 1, 1])
    cols[0].write("**Name**")
    cols[1].write("**Excess Penalty**")
    cols[2].write("**Actions**")

    for i, bus in enumerate(st.session_state.flow_system.buses.values()):
        cols = st.columns([3, 1, 1])
        cols[0].write(bus.label_full)
        cols[1].write(f"{bus.excess_penalty_per_flow_hour:.1e}")

        # Action buttons
        if cols[2].button("Delete", key=f"delete_bus_{bus.label_full}"):
            delete_element(bus.label_full, 'buses')
            st.rerun()
