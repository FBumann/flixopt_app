import streamlit as st
import flixopt as fx
import numpy as np
import plotly.express as px
import pandas as pd

from .components import delete_component
from utils.session_state import add_element
from ui.profile_editor import time_profile_editor, smart_numeric_input

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
    """UI for creating a source component with smart numeric inputs"""
    st.title("Create Source")

    # Basic parameters
    source_name = st.text_input("Source Name", value="Source A", key="source_name")

    source_bus = st.selectbox("Energy Bus", list(st.session_state.flow_system.buses), key="source_bus")

    # Source size parameter using smart input
    source_size = smart_numeric_input(
        "Source Size",
        key="source_size",
        default_value=1.0,
        description="Size [kW]",
    )

    fixed_relative_profile = smart_numeric_input(
        "Fixed relative profile",
        key="Source_profile",
        default_value=1.0,
        description="Fixed relative profile [kW/size]",
        timesteps=st.session_state.timesteps
    )


    # Effects per flow hour
    st.write("## Effects per Flow Hour")
    effects_per_flow_hour = {}

    for effect in list(st.session_state.flow_system.effects):
        # Each effect can also be a time series
        effect_value = smart_numeric_input(
            effect.label_full,
            key=f"effect_{effect.label_full}",
            description=f"Effect per flow hour for {effect.label_full}",
            timesteps=st.session_state.timesteps if hasattr(st.session_state, 'timesteps') else None
        )

        if not isinstance(effect_value, (int, float)) or effect_value != 0:
            effects_per_flow_hour[effect.label_full] = effect_value

    # Create instance button
    if st.button("Add Source"):
        if not hasattr(st.session_state, 'flow_system') or st.session_state.flow_system is None:
            st.error("Please initialize the flow system first.")
        else:
            try:
                new_source = fx.Source(
                    label=source_name, 
                    source=fx.Flow(
                        'source',
                        bus=source_bus,
                        size=source_size,
                        effects_per_flow_hour=effects_per_flow_hour,
                        fixed_relative_profile=fixed_relative_profile,
                    )
                )

                success, message = add_element(new_source, 'sources')

                if success:
                    st.success(message)
                else:
                    st.error(message)
            except Exception as e:
                st.error(f"Error adding source: {str(e)}")

def create_sink_ui():
    """UI for creating a source component with smart numeric inputs"""
    st.title("Create Source")

    # Basic parameters
    sink_name = st.text_input("Source Name", value="Source A", key="sink_name")

    sink_bus = st.selectbox("Energy Bus", list(st.session_state.flow_system.buses), key="sink_bus")

    # Source size parameter using smart input
    sink_size = smart_numeric_input(
        "Sink Size",
        key="Sink_size",
        default_value=1.0,
        description="Size [kW]",
        timesteps=st.session_state.timesteps
    )

    fixed_relative_profile = smart_numeric_input(
        "Fixed relative profile",
        key="Sink_profile",
        default_value=1.0,
        description="Fixed relative profile [kW/size]",
        timesteps=st.session_state.timesteps
    )

    # Effects per flow hour
    st.write("## Effects per Flow Hour")
    effects_per_flow_hour = {}

    if hasattr(st.session_state, 'flow_system') and hasattr(st.session_state.flow_system, 'effects'):
        for effect in list(st.session_state.flow_system.effects):
            # Each effect can also be a time series
            effect_value = smart_numeric_input(
                effect.label_full,
                key=f"effect_{effect.label_full}",
                description=f"Effect per flow hour for {effect.label_full}",
                timesteps=st.session_state.timesteps if hasattr(st.session_state, 'timesteps') else None
            )

            if not isinstance(effect_value, (int, float)) or effect_value != 0:
                effects_per_flow_hour[effect.label_full] = effect_value

    # Create instance button
    if st.button("Add Sink"):
        if not hasattr(st.session_state, 'flow_system') or st.session_state.flow_system is None:
            st.error("Please initialize the flow system first.")
        else:
            try:
                new_source = fx.Sink(
                    label=sink_name,
                    sink=fx.Flow(
                        'sink',
                        bus=sink_bus,
                        size=sink_size,
                        effects_per_flow_hour=effects_per_flow_hour,
                        fixed_relative_profile=fixed_relative_profile,
                    )
                )

                success, message = add_element(new_source, 'sinks')

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
        if st.session_state.elements['sources']:
            st.write("Current Sources:")

            # Create a table of sources with options to delete
            for i, source in enumerate(st.session_state.flow_system.components.values()):
                if not isinstance(source, fx.Source):
                    continue
                cols = st.columns([3, 1])
                cols[0].write(f"{i+1}. {source.label_full}")

                if cols[1].button("Delete", key=f"delete_source_{source.label_full}"):
                    delete_component(source.label_full)
                    st.rerun()

    with col2:
        if st.session_state.elements['sinks']:
            st.write("Current Sinks:")

            # Create a table of sinks with options to delete
            for i, sink in enumerate(st.session_state.elements['sinks']):
                cols = st.columns([3, 1])
                cols[0].write(f"{i+1}. {sink.label}")

                if cols[1].button("Delete", key=f"delete_sink_{i}"):
                    delete_component(sink, 'sinks', i)
                    st.rerun()
