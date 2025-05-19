import streamlit as st
import flixopt as fx

from ui.profile_editor import smart_numeric_input, dict_editor

# Function to create a Flow configuration UI
def create_flow_ui(prefix="flow", default_name="NewFlow", description=None):
    """
    Creates a modular Flow configuration UI that can be reused in different components.

    Parameters:
    -----------
    prefix : str
        Prefix for session state keys to allow multiple instances
    default_name : str
        Default name for the flow
    parent_name : str or None
        Name of the parent component, used to suggest flow name
    description : str or None
        Optional description text

    Returns:
    --------
    dict
        Dictionary of flow parameters to pass to Flow constructor
    """
    flow_params = {}

    # Basic Flow Parameters
    st.subheader("Flow Configuration")
    if description:
        st.info(description)

    # Generate default name based on parent if provided
    flow_name = st.text_input("Flow Name", value=default_name, key=f"{prefix}_name")
    flow_params["label"] = flow_name

    # Bus selection
    flow_bus = st.selectbox("Bus Connection",
                            options=st.session_state.elements["buses"],
                            key=f"{prefix}_bus")

    flow_params["bus"] = flow_bus

    # Use smart_numeric_input for size
    flow_size = smart_numeric_input(
        "Flow Size",
        key=f"{prefix}_size",
        default_value=1000.0,
        description="Maximum size in kW",
        timesteps=st.session_state.timesteps if "timesteps" in st.session_state else None
    )
    flow_params["size"] = flow_size

    # Flow Profile Settings
    with st.expander("Flow Profile Settings", expanded=False):
        use_profile = st.checkbox("Use Fixed Relative Profile", key=f"{prefix}_use_profile")

        if use_profile:
            fixed_profile = smart_numeric_input(
                "Fixed Relative Profile",
                key=f"{prefix}_fixed_profile",
                default_value=1.0,
                description="Fixed profile that scales with size",
                timesteps=st.session_state.timesteps if "timesteps" in st.session_state else None
            )
            flow_params["fixed_relative_profile"] = fixed_profile
        else:
            col1, col2 = st.columns(2)
            with col1:
                relative_min = smart_numeric_input(
                    "Relative Minimum",
                    key=f"{prefix}_relative_min",
                    default_value=0.0,
                    description="Minimum value relative to size",
                    timesteps=st.session_state.timesteps if "timesteps" in st.session_state else None
                )
                flow_params["relative_minimum"] = relative_min

            with col2:
                relative_max = smart_numeric_input(
                    "Relative Maximum",
                    key=f"{prefix}_relative_max",
                    default_value=1.0,
                    description="Maximum value relative to size",
                    timesteps=st.session_state.timesteps if "timesteps" in st.session_state else None
                )
                flow_params["relative_maximum"] = relative_max

    # Operational Constraints
    with st.expander("Operational Constraints", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            flow_hours_min = st.number_input(
                "Minimum Flow Hours",
                min_value=0.0,
                value=0.0,
                help="Minimum total flow-hours required",
                key=f"{prefix}_flow_hours_min"
            )
            if flow_hours_min > 0:
                flow_params["flow_hours_total_min"] = flow_hours_min

        with col2:
            flow_hours_max = st.number_input(
                "Maximum Flow Hours",
                min_value=0.0,
                value=0.0,
                help="Maximum total flow-hours allowed (0 = no limit)",
                key=f"{prefix}_flow_hours_max"
            )
            if flow_hours_max > 0:
                flow_params["flow_hours_total_max"] = flow_hours_max

        col1, col2 = st.columns(2)
        with col1:
            load_factor_min = st.number_input(
                "Minimum Load Factor",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                help="Minimum average flow / size",
                key=f"{prefix}_load_factor_min"
            )
            if load_factor_min > 0:
                flow_params["load_factor_min"] = load_factor_min

        with col2:
            load_factor_max = st.number_input(
                "Maximum Load Factor",
                min_value=0.0,
                max_value=1.0,
                value=1.0,
                help="Maximum average flow / size",
                key=f"{prefix}_load_factor_max"
            )
            if load_factor_max < 1.0:
                flow_params["load_factor_max"] = load_factor_max

    # Cost Parameters
    with st.expander("Effects per flow hour", expanded=False):

        effects_dict = dict_editor(
            "Effects per Flow Hour",
            key=f"{prefix}_effects",
            available_effects=st.session_state.elements['effects'],
            timesteps=st.session_state.timesteps if "timesteps" in st.session_state else None
        )

        if effects_dict:
            flow_params["effects_per_flow_hour"] = effects_dict

    # On/Off Behavior
    with st.expander("On/Off Behavior", expanded=False):
        use_on_off = st.checkbox("Enable On/Off Behavior", key=f"{prefix}_use_on_off")

        if use_on_off:
            col1, col2 = st.columns(2)
            with col1:
                min_uptime = st.number_input(
                    "Minimum Uptime [h]",
                    min_value=0,
                    value=1,
                    help="Minimum number of hours the flow must remain on once started",
                    key=f"{prefix}_min_uptime"
                )

            with col2:
                min_downtime = st.number_input(
                    "Minimum Downtime [h]",
                    min_value=0,
                    value=1,
                    help="Minimum number of hours the flow must remain off once stopped",
                    key=f"{prefix}_min_downtime"
                )

            startup_effects = dict_editor(
                "Startup Effects",
                key=f"{prefix}_startup_effects",
                available_effects=st.session_state.elements['effects'],
                timesteps=st.session_state.timesteps
            )

            effects_per_running_hour = dict_editor(
                "Effects per running hour",
                key=f"{prefix}_effects_per_running_hour",
                available_effects=st.session_state.elements['effects'],
                timesteps=st.session_state.timesteps
            )

            on_off_params = {
                "consecutive_on_hours_min": min_uptime,
                "consecutive_off_hours_min": min_downtime,
                "effects_per_switch_on": startup_effects,
                "effects_per_running_hour": effects_per_running_hour,
            }
            # We'll need to import fx.OnOffParameters in the calling code
            # Just store the params here
            flow_params["on_off_parameters"] = on_off_params

    # Advanced Settings
    with st.expander("Advanced Settings", expanded=False):
        # Previous flow rate
        use_prev_flow = st.checkbox("Specify Previous Flow Rate", key=f"{prefix}_use_prev_flow")

        if use_prev_flow:
            prev_flow_rate = smart_numeric_input(
                "Previous Flow Rate",
                key=f"{prefix}_prev_flow_rate",
                default_value=0.0,
                description="Used for determining how long the flow has been on/off",
                timesteps=st.session_state.timesteps if "timesteps" in st.session_state else None
            )
            flow_params["previous_flow_rate"] = prev_flow_rate

        # Meta data
        use_meta = st.checkbox("Add Meta Data", key=f"{prefix}_use_meta")

        if use_meta:
            meta_data = {}
            with st.container():
                st.write("##### Meta Data")
                meta_keys = st.text_input("Keys (comma-separated)", key=f"{prefix}_meta_keys")

                if meta_keys:
                    keys = [k.strip() for k in meta_keys.split(",")]
                    for key in keys:
                        meta_data[key] = st.text_input(f"Value for {key}", key=f"{prefix}_{key}")

            flow_params["meta_data"] = meta_data

    return flow_params
