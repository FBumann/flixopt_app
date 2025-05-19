import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

def time_profile_editor(timesteps, key_prefix="profile", default_value=1.0,
                        title="Time Profile", show_preview=True, in_form=True):
    """
    Reusable time profile editor component that works inside forms.

    Parameters:
    -----------
    timesteps : pandas.DatetimeIndex
        The timesteps for which the profile should be created
    key_prefix : str
        Prefix for unique Streamlit widget keys
    default_value : float
        Default value for the profile points
    title : str
        Title for the profile section
    show_preview : bool
        Whether to show a preview chart of the profile
    in_form : bool
        Whether this component is being used inside a form

    Returns:
    --------
    numpy.ndarray or None
        The created profile values
    """
    if timesteps is None or len(timesteps) == 0:
        st.warning("No timesteps available. Please initialize the system first.")
        return None

    # Initialize session state for this profile editor instance
    profile_key = f"{key_prefix}_profile_data"
    use_profile_key = f"{key_prefix}_use"
    profile_type_key = f"{key_prefix}_type"

    # Initialize session state variables if they don't exist
    if profile_key not in st.session_state:
        st.session_state[profile_key] = np.ones(len(timesteps)) * default_value
    if use_profile_key not in st.session_state:
        st.session_state[use_profile_key] = False
    if profile_type_key not in st.session_state:
        st.session_state[profile_type_key] = "Constant"

    # Create UI
    st.subheader(title)
    use_profile = st.checkbox("Use Time-Dependent Profile",
                              value=st.session_state[use_profile_key],
                              key=use_profile_key)

    if not use_profile:
        return None

    profile_type = st.selectbox("Profile Type",
                                ["Constant", "Sinusoidal", "Manual Entry"],
                                key=profile_type_key)

    # Handle the different profile types
    if profile_type == "Constant":
        # Define callback to update profile when value changes
        def update_constant(value):
            st.session_state[profile_key] = np.ones(len(timesteps)) * value

        profile_value = st.number_input("Constant Value",
                                        min_value=0.0,
                                        max_value=1.0,
                                        value=default_value,
                                        key=f"{key_prefix}_constant",
                                        on_change=update_constant if not in_form else None,
                                        args=[] if in_form else [st.session_state[f"{key_prefix}_constant"]])

        if in_form:
            st.session_state[profile_key] = np.ones(len(timesteps)) * profile_value

    elif profile_type == "Sinusoidal":
        # Store parameters in session state
        for param in ["amplitude", "periods", "offset", "phase"]:
            if f"{key_prefix}_{param}" not in st.session_state:
                default_vals = {"amplitude": 0.5, "periods": 1, "offset": 0.5, "phase": 0.0}
                st.session_state[f"{key_prefix}_{param}"] = default_vals.get(param, 0.5)

        col1, col2 = st.columns(2)
        with col1:
            amplitude = st.slider("Amplitude",
                                  min_value=0.0,
                                  max_value=1.0,
                                  value=st.session_state[f"{key_prefix}_amplitude"],
                                  step=0.01,
                                  key=f"{key_prefix}_amplitude")
            periods = st.slider("Periods",
                                min_value=1,
                                max_value=5,
                                value=st.session_state[f"{key_prefix}_periods"],
                                key=f"{key_prefix}_periods")
        with col2:
            offset = st.slider("Offset",
                               min_value=0.0,
                               max_value=1.0,
                               value=st.session_state[f"{key_prefix}_offset"],
                               step=0.01,
                               key=f"{key_prefix}_offset")
            phase = st.slider("Phase Shift",
                              min_value=0.0,
                              max_value=2*np.pi,
                              value=st.session_state[f"{key_prefix}_phase"],
                              step=0.1,
                              key=f"{key_prefix}_phase")

        # Update the profile data
        t = np.linspace(0, 2*np.pi*periods, len(timesteps))
        st.session_state[profile_key] = offset + amplitude * np.sin(t + phase)

    else:  # Manual Entry
        st.write("Enter values for each time step:")

        # Option to upload CSV or Excel file with profile data
        st.write("Or upload a file with profile data:")
        uploaded_file = st.file_uploader("Upload CSV or Excel",
                                         type=["csv", "xlsx", "xls"],
                                         key=f"{key_prefix}_upload")

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    profile_data = pd.read_csv(uploaded_file, index_col=0)
                else:
                    profile_data = pd.read_excel(uploaded_file, index_col=0)

                # Try to match with timesteps
                if profile_data.shape[0] >= len(timesteps):
                    st.session_state[profile_key] = profile_data.iloc[:len(timesteps), 0].values
                    st.success(f"Loaded profile with {len(st.session_state[profile_key])} values.")
                else:
                    st.warning(f"Uploaded profile has only {profile_data.shape[0]} values, but {len(timesteps)} are needed.")
            except Exception as e:
                st.error(f"Error loading profile: {str(e)}")
        else:
            # Show a sample of time steps for manual entry
            max_display = min(24, len(timesteps))  # Limit number displayed for usability

            # Initialize individual time point values if not present
            for i in range(max_display):
                manual_key = f"{key_prefix}_manual_{i}"
                if manual_key not in st.session_state:
                    st.session_state[manual_key] = default_value

            # Show manual entry fields
            for i in range(max_display):
                manual_key = f"{key_prefix}_manual_{i}"

                def update_point(i, value):
                    profile = st.session_state[profile_key].copy()
                    profile[i] = value
                    st.session_state[profile_key] = profile

                value = st.number_input(
                    f"Value at {timesteps[i]}",
                    min_value=0.0,
                    max_value=1.0,
                    value=st.session_state[manual_key],
                    key=manual_key
                )

                # Update the profile in session state
                if in_form:
                    temp_profile = st.session_state[profile_key].copy()
                    temp_profile[i] = value
                    st.session_state[profile_key] = temp_profile

            if len(timesteps) > max_display:
                st.info(f"Only showing first {max_display} of {len(timesteps)} time steps for manual entry.")

    # Preview the profile
    if show_preview:
        st.subheader("Profile Preview")
        fig = px.line(
            x=timesteps,
            y=st.session_state[profile_key],
            labels={"x": "Time", "y": "Relative Value"}
        )
        st.plotly_chart(fig, use_container_width=True)

    # Return the profile data from session state
    return st.session_state[profile_key]
