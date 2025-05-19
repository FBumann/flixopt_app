import streamlit as st
import flixopt as fx
from utils.session_state import add_component

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
            success, message = add_component(new_bus, 'buses')

            if success:
                st.success(message)
            else:
                st.error(message)

    # Display existing buses
    display_existing_buses()

def display_existing_buses():
    """Display the list of existing buses"""
    if not st.session_state.components['buses']:
        return

    st.write("Current Buses:")

    # Create a table of buses with options to edit/delete
    cols = st.columns([3, 1, 1])
    cols[0].write("**Name**")
    cols[1].write("**Excess Penalty**")
    cols[2].write("**Actions**")

    for i, bus in enumerate(st.session_state.components['buses']):
        cols = st.columns([3, 1, 1])
        cols[0].write(bus.label)
        cols[1].write(f"{bus.excess_penalty_per_flow_hour:.1e}")

        # Action buttons
        if cols[2].button("Delete", key=f"delete_bus_{i}"):
            delete_bus(i)
            st.rerun()

def delete_bus(index):
    """Delete a bus from the system"""
    try:
        # Before deleting, check if the bus is in use
        bus_to_delete = st.session_state.components['buses'][index]

        # Check if bus is in use by any component
        in_use = False
        usage = []

        for component_type in ['converters', 'storages', 'sources', 'sinks']:
            for component in st.session_state.components[component_type]:
                if hasattr(component, 'flow'):
                    for flow in component.flow:
                        if hasattr(flow, 'bus') and flow.bus == bus_to_delete.label:
                            in_use = True
                            usage.append(f"{component.label} ({flow.label})")

        if in_use:
            st.error(f"Cannot delete bus '{bus_to_delete.label}' as it is used by: {', '.join(usage)}")
            return False

        # If not in use, remove it
        st.session_state.flow_system.remove_elements(bus_to_delete)
        st.session_state.components['buses'].pop(index)
        return True
    except Exception as e:
        st.error(f"Error deleting bus: {str(e)}")
        return False