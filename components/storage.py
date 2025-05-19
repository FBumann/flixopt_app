import streamlit as st
import flixopt as fx
from utils.session_state import add_element, delete_element

def create_storage_ui():
    """UI for creating and managing storage systems"""
    st.subheader("Storage Systems")
    st.write("Storage systems store energy for later use.")

    # If no buses exist, inform the user
    if not st.session_state.elements['buses']:
        st.warning("Please create at least one bus before adding storage systems.")
        return

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

        # Advanced settings
        with st.expander("Advanced Settings"):
            col1, col2 = st.columns(2)
            with col1:
                min_charge_state = st.number_input("Minimum Charge State (kWh)", min_value=0.0, value=0.0)
                final_charge_state = st.number_input("Final Charge State (kWh)", min_value=0.0, value=None,
                                                     help="Target charge state at the end of the optimization period")
            with col2:
                custom_capacity_flow_hours = st.checkbox("Custom Capacity in Flow Hours", value=False,
                                                         help="Specify capacity in flow hours instead of kWh")
                if custom_capacity_flow_hours:
                    capacity_flow_hours = st.number_input("Capacity in Flow Hours", min_value=0.1, value=capacity/charge_rate)
                else:
                    capacity_flow_hours = capacity / charge_rate

            # Effects for charging and discharging
            st.subheader("Charging/Discharging Effects")

            charge_effects = {}
            discharge_effects = {}

            if st.session_state.elements['effects']:
                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Charging Effects:**")
                    for effect in st.session_state.elements['effects']:
                        value = st.number_input(f"{effect} per kWh (Charging)",
                                                value=0.0,
                                                key=f"storage_charge_{effect}")
                        if value != 0:
                            charge_effects[effect] = value

                with col2:
                    st.write("**Discharging Effects:**")
                    for effect in st.session_state.elements['effects']:
                        value = st.number_input(f"{effect} per kWh (Discharging)",
                                                value=0.0,
                                                key=f"storage_discharge_{effect}")
                        if value != 0:
                            discharge_effects[effect] = value

        if st.form_submit_button("Add Storage"):
            if st.session_state.flow_system is None:
                st.error("Please initialize the flow system first.")
                return

            try:
                # Create storage system
                charging_flow = fx.Flow(
                    f'{storage_name}_charging',
                    bus=storage_bus,
                    size=charge_rate,
                    effects_per_flow_hour=charge_effects if charge_effects else None
                )

                discharging_flow = fx.Flow(
                    f'{storage_name}_discharging',
                    bus=storage_bus,
                    size=discharge_rate,
                    effects_per_flow_hour=discharge_effects if discharge_effects else None
                )

                new_storage = fx.Storage(
                    storage_name,
                    charging=charging_flow,
                    discharging=discharging_flow,
                    capacity_in_flow_hours=capacity_flow_hours,
                    initial_charge_state=initial_charge * capacity,
                    eta_charge=eta_charge,
                    eta_discharge=eta_discharge,
                    relative_loss_per_hour=loss_rate,
                    prevent_simultaneous_charge_and_discharge=prevent_simultaneous,
                    minimum_charge_state=min_charge_state,
                    final_charge_state=final_charge_state if final_charge_state is not None else None
                )

                success, message = add_element(new_storage, 'storages')

                if success:
                    st.success(message)
                else:
                    st.error(message)
            except Exception as e:
                st.error(f"Error adding storage: {str(e)}")

    # Display existing storage systems
    display_existing_storage()

def display_existing_storage():
    """Display the list of existing storage systems"""
    if not st.session_state.elements['storages']:
        return

    st.write("Current Storage Systems:")

    # Create a table of storage systems with options to edit/delete
    cols = st.columns([3, 1, 1, 1, 1])
    cols[0].write("**Name**")
    cols[1].write("**Bus**")
    cols[2].write("**Capacity**")
    cols[3].write("**Efficiency**")
    cols[4].write("**Actions**")

    for i, storage in enumerate(st.session_state.elements['storages']):
        cols = st.columns([3, 1, 1, 1, 1])
        cols[0].write(storage.label)

        # Get the bus from the charging flow
        if hasattr(storage, 'charging') and hasattr(storage.charging, 'bus'):
            cols[1].write(f"{storage.charging.bus}")
        else:
            cols[1].write("N/A")

        # Get capacity
        if hasattr(storage, 'capacity_in_flow_hours') and hasattr(storage.charging, 'size'):
            capacity = storage.capacity_in_flow_hours * storage.charging.size
            cols[2].write(f"{capacity:.1f} kWh")
        else:
            cols[2].write("N/A")

        # Show efficiencies
        if hasattr(storage, 'eta_charge') and hasattr(storage, 'eta_discharge'):
            round_trip = storage.eta_charge * storage.eta_discharge
            cols[3].write(f"{round_trip:.0%}")
        else:
            cols[3].write("N/A")

        # Action buttons
        if cols[4].button("Delete", key=f"delete_storage_{i}"):
            delete_element(i)
            st.rerun()

        # Show details in an expander
        with st.expander(f"Details: {storage.label}"):
            # Basic information
            st.write("**Basic Information:**")
            st.write(f"- Capacity: {storage.capacity_in_flow_hours * storage.charging.size:.1f} kWh")
            st.write(f"- Initial Charge: {storage.initial_charge_state:.1f} kWh")

            if hasattr(storage, 'minimum_charge_state'):
                st.write(f"- Minimum Charge: {storage.minimum_charge_state:.1f} kWh")

            if hasattr(storage, 'final_charge_state') and storage.final_charge_state is not None:
                st.write(f"- Final Charge: {storage.final_charge_state:.1f} kWh")

            st.write(f"- Relative Loss: {storage.relative_loss_per_hour:.1%} per hour")
            st.write(f"- Prevent Simultaneous Charge/Discharge: {storage.prevent_simultaneous_charge_and_discharge}")

            # Charging information
            st.write("\n**Charging:**")
            st.write(f"- Max Rate: {storage.charging.size:.1f} kW")
            st.write(f"- Efficiency: {storage.eta_charge:.0%}")

            if hasattr(storage.charging, 'effects_per_flow_hour') and storage.charging.effects_per_flow_hour:
                st.write("- Effects:")
                for effect, value in storage.charging.effects_per_flow_hour.items():
                    st.write(f"  - {effect}: {value}")

            # Discharging information
            st.write("\n**Discharging:**")
            st.write(f"- Max Rate: {storage.discharging.size:.1f} kW")
            st.write(f"- Efficiency: {storage.eta_discharge:.0%}")

            if hasattr(storage.discharging, 'effects_per_flow_hour') and storage.discharging.effects_per_flow_hour:
                st.write("- Effects:")
                for effect, value in storage.discharging.effects_per_flow_hour.items():
                    st.write(f"  - {effect}: {value}")
