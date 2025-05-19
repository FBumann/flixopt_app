import streamlit as st
import flixopt as fx
import numpy as np
from utils.session_state import add_component
from ui.profile_editor import time_profile_editor

def create_sources_sinks_ui():
    """UI for creating and managing sources and sinks"""
    st.subheader("Sources and Sinks")
    st.write("Sources provide energy to the system; sinks consume energy from the system.")

    component_type = st.radio("Component Type", ["Source", "Sink"])

    if component_type == "Source":
        create_source_ui()
    else:
        create_sink_ui()

    # Display existing sources and sinks
    display_existing_sources_sinks()

def create_source_ui():
    """UI for creating a source component"""
    with st.form("source_form"):
        source_name = st.text_input("Source Name", value="Source")

        # Check if we have any buses
        if not st.session_state.components['buses']:
            st.warning("Please create at least one bus first.")
            st.form_submit_button("Add Source", disabled=True)
            return

        source_bus = st.selectbox("Energy Bus",
                                  list(st.session_state.flow_system.buses))

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

        # Use the reusable time profile editor - now form compatible
        profile_key = "source_profile"
        time_profile_editor(
            st.session_state.timesteps,
            key_prefix=profile_key,
            default_value=1.0,
            title="Time Profile",
            in_form=True
        )

        submitted = st.form_submit_button("Add Source")

        if submitted:
            if st.session_state.flow_system is None:
                st.error("Please initialize the flow system first.")
                return

            try:
                # Get profile from session state
                profile = st.session_state.get(f"{profile_key}_profile_data") if st.session_state.get(f"{profile_key}_use", False) else None

                # Create flow
                if profile is not None:
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

                success, message = add_component(new_source, 'sources')

                if success:
                    st.success(message)
                else:
                    st.error(message)
            except Exception as e:
                st.error(f"Error adding source: {str(e)}")

def create_sink_ui():
    """UI for creating a sink component"""
    with st.form("sink_form"):
        sink_name = st.text_input("Sink Name", value="Sink")

        # Check if we have any buses
        if not st.session_state.components['buses']:
            st.warning("Please create at least one bus first.")
            st.form_submit_button("Add Sink", disabled=True)
            return

        sink_bus = st.selectbox("Energy Bus",
                                list(st.session_state.flow_system.buses))

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

        # Use the reusable time profile editor for demand
        profile = time_profile_editor(
            st.session_state.timesteps,
            key_prefix="sink_profile",
            default_value=1.0,
            title="Demand Profile"
        )

        # Always use a profile for sinks (default to constant if not specified)
        if profile is None:
            profile = np.ones(len(st.session_state.timesteps))

        if st.form_submit_button("Add Sink"):
            if st.session_state.flow_system is None:
                st.error("Please initialize the flow system first.")
                return

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

                success, message = add_component(new_sink, 'sinks')

                if success:
                    st.success(message)
                else:
                    st.error(message)
            except Exception as e:
                st.error(f"Error adding sink: {str(e)}")

def display_existing_sources_sinks():
    """Display the list of existing sources and sinks"""
    col1, col2 = st.columns(2)

    with col1:
        if st.session_state.components['sources']:
            st.write("Current Sources:")

            # Create a table of sources with options to delete
            for i, source in enumerate(st.session_state.components['sources']):
                cols = st.columns([3, 1])
                cols[0].write(f"{i+1}. {source.label}")

                if cols[1].button("Delete", key=f"delete_source_{i}"):
                    delete_component(source, 'sources', i)
                    st.rerun()

    with col2:
        if st.session_state.components['sinks']:
            st.write("Current Sinks:")

            # Create a table of sinks with options to delete
            for i, sink in enumerate(st.session_state.components['sinks']):
                cols = st.columns([3, 1])
                cols[0].write(f"{i+1}. {sink.label}")

                if cols[1].button("Delete", key=f"delete_sink_{i}"):
                    delete_component(sink, 'sinks', i)
                    st.rerun()

def delete_component(component, component_type, index):
    """Delete a component from the system"""
    try:
        st.session_state.flow_system.remove_elements(component)
        st.session_state.components[component_type].pop(index)
        return True
    except Exception as e:
        st.error(f"Error deleting component: {str(e)}")
        return False