import streamlit as st
import flixopt as fx
import numpy as np
import plotly.express as px
import pandas as pd

from .components import delete_component
from utils.session_state import add_element
from ui.profile_editor import time_profile_editor, smart_numeric_input, dict_editor

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
    st.title("Create Source")

    # Create a container for the source UI
    source_container = st.container()

    with source_container:
        # LAYER 1: Basic Source Information
        st.subheader("Basic Source Information")
        source_name = st.text_input("Source Name", value="NewSource", key="source_name")
        st.info("A Source is a component that generates energy or material and outputs it to a bus.")

        # Create timestamp data for time series
        if "timesteps" not in st.session_state:
            st.session_state.timesteps = pd.date_range(
                start="2023-01-01",
                periods=24,
                freq="H"
            )

        # LAYER 2: Basic Flow Parameters
        st.subheader("Flow Configuration")
        flow_name = st.text_input("Flow Name", value=f"{source_name}_flow", key="flow_name")
        flow_bus = st.selectbox("Bus Connection",
                                options=st.session_state.elements['buses'],
                                key="flow_bus")

        # Use smart_numeric_input for size
        flow_size = smart_numeric_input(
            "Flow Size",
            key="flow_size",
            default_value=1000.0,
            description="Maximum size in kW",
            timesteps=st.session_state.timesteps
        )

        # LAYER 3: Flow Profile Settings
        with st.expander("Flow Profile Settings", expanded=False):
            use_profile = st.checkbox("Use Fixed Relative Profile", key="use_profile")

            if use_profile:
                fixed_profile = smart_numeric_input(
                    "Fixed Relative Profile",
                    key="fixed_profile",
                    default_value=1.0,
                    description="Fixed profile that scales with size",
                    timesteps=st.session_state.timesteps
                )
            else:
                fixed_profile = None

                col1, col2 = st.columns(2)
                with col1:
                    relative_min = smart_numeric_input(
                        "Relative Minimum",
                        key="relative_min",
                        default_value=0.0,
                        description="Minimum value relative to size",
                        timesteps=st.session_state.timesteps
                    )

                with col2:
                    relative_max = smart_numeric_input(
                        "Relative Maximum",
                        key="relative_max",
                        default_value=1.0,
                        description="Maximum value relative to size",
                        timesteps=st.session_state.timesteps
                    )

        # LAYER 4: Operational Constraints
        with st.expander("Operational Constraints", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                flow_hours_min = st.number_input(
                    "Minimum Flow Hours",
                    min_value=0.0,
                    value=0.0,
                    help="Minimum total flow-hours required",
                    key="flow_hours_min"
                )

            with col2:
                flow_hours_max = st.number_input(
                    "Maximum Flow Hours",
                    min_value=0.0,
                    value=0.0,
                    help="Maximum total flow-hours allowed (0 = no limit)",
                    key="flow_hours_max"
                )

            col1, col2 = st.columns(2)
            with col1:
                load_factor_min = st.number_input(
                    "Minimum Load Factor",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.0,
                    help="Minimum average flow / size",
                    key="load_factor_min"
                )

            with col2:
                load_factor_max = st.number_input(
                    "Maximum Load Factor",
                    min_value=0.0,
                    max_value=1.0,
                    value=1.0,
                    help="Maximum average flow / size",
                    key="load_factor_max"
                )

        # LAYER 5: Cost Parameters
        with st.expander("Cost Parameters", expanded=False):
            # Define available effects (this would come from your system)
            if "available_effects" not in st.session_state:
                st.session_state.available_effects = ["Cost", "CO2", "PrimaryEnergy"]

            effects_dict = dict_editor(
                "Effects per Flow Hour",
                key="effects",
                available_effects=st.session_state.available_effects,
                timesteps=st.session_state.timesteps
            )

        # LAYER 6: On/Off Behavior
        with st.expander("On/Off Behavior", expanded=False):
            use_on_off = st.checkbox("Enable On/Off Behavior", key="use_on_off")

            if use_on_off:
                col1, col2 = st.columns(2)
                with col1:
                    min_uptime = st.number_input(
                        "Minimum Uptime",
                        min_value=0,
                        value=1,
                        help="Minimum number of timesteps the flow must remain on once started",
                        key="min_uptime"
                    )

                with col2:
                    min_downtime = st.number_input(
                        "Minimum Downtime",
                        min_value=0,
                        value=1,
                        help="Minimum number of timesteps the flow must remain off once stopped",
                        key="min_downtime"
                    )

                startup_cost = st.number_input(
                    "Startup Cost",
                    min_value=0.0,
                    value=0.0,
                    help="Cost incurred when starting the flow",
                    key="startup_cost"
                )

                on_off_params = {
                    "min_uptime": min_uptime,
                    "min_downtime": min_downtime,
                    "startup_cost": startup_cost
                }
            else:
                on_off_params = None

        # LAYER 7: Advanced Settings
        with st.expander("Advanced Settings", expanded=False):
            # Previous flow rate
            use_prev_flow = st.checkbox("Specify Previous Flow Rate", key="use_prev_flow")

            if use_prev_flow:
                prev_flow_rate = smart_numeric_input(
                    "Previous Flow Rate",
                    key="prev_flow_rate",
                    default_value=0.0,
                    description="Used for determining how long the flow has been on/off",
                    timesteps=st.session_state.timesteps
                )
            else:
                prev_flow_rate = None

            # Meta data
            use_meta = st.checkbox("Add Meta Data", key="use_meta")

            if use_meta:
                meta_data = {}
                with st.container():
                    st.write("##### Meta Data")
                    meta_keys = st.text_input("Keys (comma-separated)", key="meta_keys")

                    if meta_keys:
                        keys = [k.strip() for k in meta_keys.split(",")]
                        for key in keys:
                            meta_data[key] = st.text_input(f"Value for {key}", key=f"meta_{key}")
            else:
                meta_data = None

        # Create button
        if st.button("Create Source", key="create_source"):
            try:
                # Create Flow object
                # First handle optional parameters
                flow_args = {
                    "label": flow_name,
                    "bus": flow_bus,
                    "size": flow_size,
                }

                # Add optional flow profile parameters
                if use_profile:
                    flow_args["fixed_relative_profile"] = fixed_profile
                else:
                    flow_args["relative_minimum"] = relative_min
                    flow_args["relative_maximum"] = relative_max

                # Add operational constraints if specified
                if flow_hours_min > 0:
                    flow_args["flow_hours_total_min"] = flow_hours_min
                if flow_hours_max > 0:
                    flow_args["flow_hours_total_max"] = flow_hours_max
                if load_factor_min > 0:
                    flow_args["load_factor_min"] = load_factor_min
                if load_factor_max < 1.0:
                    flow_args["load_factor_max"] = load_factor_max

                # Add effects if specified
                if effects_dict:
                    flow_args["effects_per_flow_hour"] = effects_dict

                # Add on/off parameters if specified
                if use_on_off and on_off_params:
                    flow_args["on_off_parameters"] = fx.OnOffParameters(**on_off_params)

                # Add previous flow rate if specified
                if use_prev_flow:
                    flow_args["previous_flow_rate"] = prev_flow_rate


                # Create the Flow object
                # Create the Source object
                source = fx.Source(
                    label=source_name,
                    source=fx.Flow(**flow_args),
                )

                # Display success message
                st.success(f"Successfully created Source '{source_name}' with Flow '{flow_name}'")

                # Store in session state (for your application logic)
                if "sources" not in st.session_state:
                    st.session_state.sources = {}

                st.session_state.sources[source_name] = source

                # Display representation of the created objects
                with st.expander("Created Source Details", expanded=True):
                    st.write("##### Source")
                    st.write(f"Label: {source.label}")
                    st.write(f"Outputs: {[o.label for o in source.outputs]}")
                    if meta_data:
                        st.write(f"Meta Data: {meta_data}")

                    st.write("##### Flow")
                    for key, value in flow_args.items():
                        if key not in ["on_off_parameters", "meta_data"]:
                            if isinstance(value, (np.ndarray, list)):
                                st.write(f"{key}: Array with {len(value)} values")
                            else:
                                st.write(f"{key}: {value}")

                    if "on_off_parameters" in flow_args:
                        st.write("on_off_parameters:")
                        for k, v in on_off_params.items():
                            st.write(f"  {k}: {v}")

            except Exception as e:
                st.error(f"Error creating Source: {str(e)}")

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
