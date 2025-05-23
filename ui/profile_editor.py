import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

def smart_numeric_input(label, key, default_value=0.0, description=None, timesteps=None):
    """
    Smart numeric input component that allows switching between single value and time series.

    Parameters:
    -----------
    label : str
        Label for the input field
    key : str
        Unique key for the session state
    default_value : float
        Default value for single input mode
    description : str or None
        Optional description to show below the input
    timesteps : pandas.DatetimeIndex or None
        Timesteps for time series data if applicable

    Returns:
    --------
    float or numpy.ndarray
        Single value or array of values
    """
    # Initialize session state
    if f"{key}_mode" not in st.session_state:
        st.session_state[f"{key}_mode"] = "single"

    if f"{key}_value" not in st.session_state:
        st.session_state[f"{key}_value"] = default_value

    if f"{key}_series" not in st.session_state and timesteps is not None:
        st.session_state[f"{key}_series"] = pd.DataFrame(
            {"Value": [default_value] * len(timesteps)},
            index=timesteps
        )

    if f"{key}_import_export_open" not in st.session_state:
        st.session_state[f"{key}_import_export_open"] = False

    # Create UI
    st.write(f"#### {label}")
    if description:
        st.write(description)

    # Mode selector
    if timesteps is not None:
        input_mode = st.radio(
            "Input Type",
            options=["Single Value", "Time Series"],
            horizontal=True,
            key=f"{key}_mode_selector",
            index=0 if st.session_state[f"{key}_mode"] == "single" else 1
        )
    else:
        input_mode = "Single Value"

    # Update mode in session state
    st.session_state[f"{key}_mode"] = "single" if input_mode == "Single Value" else "series"

    # Show appropriate input based on mode
    if st.session_state[f"{key}_mode"] == "single":
        value = st.number_input(
            "Value",
            value=st.session_state[f"{key}_value"],
            key=f"{key}_value_input"
        )
        st.session_state[f"{key}_value"] = value
        return value
    else:
        # Time series input
        tabs = st.tabs(["Table Editor", "Chart View", "Presets"])

        with tabs[0]:
            # Table editor
            series_df = st.data_editor(
                st.session_state[f"{key}_series"],
                use_container_width=True,
                num_rows="fixed",
                key=f"{key}_series_editor"
            )
            st.session_state[f"{key}_series"] = series_df

            # Import/Export options - directly in the tab, not in an expander
            toggle_col1, toggle_col2 = st.columns([4, 1])
            with toggle_col1:
                st.write("Import/Export Options:")
            with toggle_col2:
                if st.button("📂" if not st.session_state[f"{key}_import_export_open"] else "✖️",
                             key=f"{key}_toggle_import_export"):
                    st.session_state[f"{key}_import_export_open"] = not st.session_state[f"{key}_import_export_open"]
                    st.rerun()

            if st.session_state[f"{key}_import_export_open"]:
                col1, col2 = st.columns(2)
                with col1:
                    csv = series_df.to_csv().encode('utf-8')
                    st.download_button(
                        "Download CSV",
                        data=csv,
                        file_name=f"{key}_data.csv",
                        mime="text/csv",
                        key=f"{key}_download"
                    )

                with col2:
                    uploaded_file = st.file_uploader(
                        "Upload CSV or Excel",
                        type=["csv", "xlsx", "xls"],
                        key=f"{key}_upload"
                    )

                    if uploaded_file is not None:
                        try:
                            if uploaded_file.name.endswith('.csv'):
                                imported_data = pd.read_csv(uploaded_file, index_col=0)
                            else:
                                imported_data = pd.read_excel(uploaded_file, index_col=0)

                            # Ensure the imported data has the right column
                            if "Value" not in imported_data.columns and len(imported_data.columns) > 0:
                                imported_data = imported_data.rename(columns={imported_data.columns[0]: "Value"})

                            # Update the session state
                            st.session_state[f"{key}_series"] = imported_data
                            st.success(f"Loaded data with {len(imported_data)} values")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error importing data: {str(e)}")

        with tabs[1]:
            # Chart view
            fig = px.line(
                series_df,
                y="Value",
                labels={"index": "Time", "Value": f"{label} Value"}
            )
            st.plotly_chart(fig, use_container_width=True)

        with tabs[2]:
            # Preset patterns
            preset = st.selectbox(
                "Select Pattern",
                options=["Constant", "Sinusoidal", "Linear Ramp", "Step Function"],
                key=f"{key}_preset"
            )

            if preset == "Constant":
                const_value = st.number_input(
                    "Constant Value",
                    value=default_value,
                    key=f"{key}_preset_constant"
                )

                if st.button("Apply Constant", key=f"{key}_apply_constant"):
                    series_df["Value"] = const_value
                    st.session_state[f"{key}_series"] = series_df
                    st.rerun()

            elif preset == "Sinusoidal":
                col1, col2 = st.columns(2)
                with col1:
                    amplitude = st.slider("Amplitude", 0.0, 1.0, 0.5, 0.01, key=f"{key}_sine_amplitude")
                    periods = st.slider("Periods", 1, 10, 1, 1, key=f"{key}_sine_periods")

                with col2:
                    offset = st.slider("Offset", 0.0, 1.0, 0.5, 0.01, key=f"{key}_sine_offset")
                    phase = st.slider("Phase", 0.0, 2*np.pi, 0.0, 0.1, key=f"{key}_sine_phase")

                if st.button("Apply Sinusoidal", key=f"{key}_apply_sine"):
                    t = np.linspace(0, 2*np.pi*periods, len(timesteps))
                    values = offset + amplitude * np.sin(t + phase)
                    series_df["Value"] = values
                    st.session_state[f"{key}_series"] = series_df
                    st.rerun()

            elif preset == "Linear Ramp":
                col1, col2 = st.columns(2)
                with col1:
                    start_val = st.number_input("Start Value", value=0.0, key=f"{key}_ramp_start")
                with col2:
                    end_val = st.number_input("End Value", value=1.0, key=f"{key}_ramp_end")

                if st.button("Apply Ramp", key=f"{key}_apply_ramp"):
                    values = np.linspace(start_val, end_val, len(timesteps))
                    series_df["Value"] = values
                    st.session_state[f"{key}_series"] = series_df
                    st.rerun()

            elif preset == "Step Function":
                col1, col2 = st.columns(2)
                with col1:
                    low_val = st.number_input("Low Value", value=0.0, key=f"{key}_step_low")
                with col2:
                    high_val = st.number_input("High Value", value=1.0, key=f"{key}_step_high")

                step_point = st.slider(
                    "Step Point",
                    0, len(timesteps)-1,
                       len(timesteps)//2,
                    key=f"{key}_step_point"
                )

                if st.button("Apply Step", key=f"{key}_apply_step"):
                    values = np.array([low_val] * len(timesteps))
                    values[step_point:] = high_val
                    series_df["Value"] = values
                    st.session_state[f"{key}_series"] = series_df
                    st.rerun()

        # Return the array of values
        return series_df["Value"].values


def dict_editor(label, key, available_effects=None, timesteps=None):
    """
    Dictionary editor for key-value pairs, with support for numeric or time series values.

    Parameters:
    -----------
    label : str
        Label for the dictionary
    key : str
        Unique key for session state
    available_effects : list or None
        List of available keys to choose from
    timesteps : pandas.DatetimeIndex or None
        Timesteps for time series values

    Returns:
    --------
    dict
        Dictionary of key-value pairs
    """
    st.write(f"#### {label}")

    # Initialize session state
    if f"{key}_dict" not in st.session_state:
        st.session_state[f"{key}_dict"] = {}

    if f"{key}_adding" not in st.session_state:
        st.session_state[f"{key}_adding"] = False

    # Display existing entries
    effects_dict = st.session_state[f"{key}_dict"]

    if effects_dict:
        st.write("Current Effects:")
        for effect_name, effect_value in effects_dict.items():
            col1, col2, col3 = st.columns([3, 6, 1])
            with col1:
                st.write(f"**{effect_name}**")
            with col2:
                if isinstance(effect_value, (np.ndarray, list)):
                    st.write("Time Series Data")
                else:
                    st.write(f"Value: {effect_value}")
            with col3:
                if st.button("🗑️", key=f"remove_{key}_{effect_name}"):
                    del st.session_state[f"{key}_dict"][effect_name]
                    if f"{key}_{effect_name}_value" in st.session_state:
                        del st.session_state[f"{key}_{effect_name}_value"]
                    if f"{key}_{effect_name}_series" in st.session_state:
                        del st.session_state[f"{key}_{effect_name}_series"]
                    st.rerun()

    # Toggle adding mode
    add_col1, add_col2 = st.columns([6, 1])
    with add_col1:
        st.write("Add a new effect:")
    with add_col2:
        if st.button("➕" if not st.session_state[f"{key}_adding"] else "✖️", key=f"{key}_toggle_add"):
            st.session_state[f"{key}_adding"] = not st.session_state[f"{key}_adding"]
            st.rerun()

    # Add new entry - not in an expander
    if st.session_state[f"{key}_adding"]:
        st.markdown("---")
        if available_effects:
            # Filter out effects already added
            available = [e for e in available_effects if e not in effects_dict]
            if not available:
                st.write("All available effects have been added.")
                st.session_state[f"{key}_adding"] = False
                st.rerun()
                return effects_dict

            new_effect = st.selectbox("Select Effect", options=available, key=f"{key}_new_effect")
        else:
            new_effect = st.text_input("Effect Name", key=f"{key}_new_effect")

        if new_effect:
            effect_value = smart_numeric_input(
                f"Value for {new_effect}",
                key=f"{key}_{new_effect}",
                default_value=0.0,
                timesteps=timesteps
            )

            col1, col2 = st.columns([3, 1])
            with col1:
                pass
            with col2:
                if st.button("Add Effect", key=f"{key}_add_effect"):
                    st.session_state[f"{key}_dict"][new_effect] = effect_value
                    st.session_state[f"{key}_adding"] = False
                    st.rerun()

        st.markdown("---")

    return effects_dict
