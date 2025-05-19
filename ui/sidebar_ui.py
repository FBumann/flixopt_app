import streamlit as st
import json
import pandas as pd
from datetime import datetime
from utils.session_state import get_component_counts, validate_system, reset_system

def render_system_status():
    """Render the system status information in the sidebar"""
    st.sidebar.subheader("System Status")

    # Display component counts
    if st.session_state.flow_system is not None:
        component_counts = get_component_counts()

        # Create a formatted status display
        st.sidebar.markdown(f"""
        **System Components:**
        - Buses: {component_counts['buses']}
        - Effects: {component_counts['effects']}
        - Converters: {component_counts['converters']}
        - Storage: {component_counts['storages']}
        - Sources: {component_counts['sources']}
        - Sinks: {component_counts['sinks']}

        **Time Steps:** {len(st.session_state.timesteps) if st.session_state.timesteps is not None else 0}

        **Status:** {'Ready for optimization' if all([component_counts['buses'], component_counts['effects'],
                                                      component_counts['converters'] + component_counts['sources'] + component_counts['sinks']])
        else 'Incomplete - add more components'}
        """)
    else:
        st.sidebar.markdown("""
        **System Status:** Not initialized

        Please go to the System Configuration tab to initialize the flow system.
        """)

def render_validation():
    """Render the system validation UI in the sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("System Validation")

    if st.session_state.flow_system is None:
        st.sidebar.info("Initialize the system first to enable validation.")
        return

    if st.sidebar.button("Validate System"):
        valid, validation_issues = validate_system()

        if valid:
            st.sidebar.success("System validation passed! All components are properly connected.")
        else:
            st.sidebar.error("Validation Issues:")
            for issue in validation_issues:
                st.sidebar.warning(f"⚠️ {issue}")

def render_import_export():
    """Render the import/export UI in the sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("Import/Export System")

    # Export current system
    if st.session_state.flow_system is not None:
        if st.sidebar.button("Export Current System"):
            try:
                # Create a dictionary representation of the model
                model_config = {
                    "timesteps": {
                        "start": st.session_state.timesteps[0].strftime("%Y-%m-%d %H:%M:%S"),
                        "periods": len(st.session_state.timesteps),
                        "freq": st.session_state.timesteps.freq.freqstr if hasattr(st.session_state.timesteps, 'freq') else "h"
                    },
                    "components": {}
                }

                # Save component configurations
                for component_type, components in st.session_state.components.items():
                    model_config["components"][component_type] = []

                    for component in components:
                        # Basic component info
                        component_config = {
                            "label": component.label,
                            "type": component.__class__.__name__
                        }

                        # Add to components list
                        model_config["components"][component_type].append(component_config)

                # Convert to JSON
                model_json = json.dumps(model_config, indent=2)

                # Provide download button
                st.sidebar.download_button(
                    label="Download Configuration JSON",
                    data=model_json,
                    file_name="flixopt_system.json",
                    mime="application/json"
                )
            except Exception as e:
                st.sidebar.error(f"Error exporting system: {str(e)}")

    # Import system from JSON
    uploaded_file = st.sidebar.file_uploader("Import System Configuration", type="json")
    if uploaded_file is not None:
        try:
            # Load the JSON data
            config_data = json.load(uploaded_file)

            # Verify the data structure
            if "timesteps" in config_data and "components" in config_data:
                if st.sidebar.button("Apply Imported Configuration"):
                    # Reset current system
                    reset_system()

                    # Create new timesteps
                    start = datetime.strptime(config_data["timesteps"]["start"], "%Y-%m-%d %H:%M:%S")
                    periods = config_data["timesteps"]["periods"]
                    freq = config_data["timesteps"]["freq"]

                    # Initialize the system
                    from utils.session_state import initialize_flow_system
                    success, message = initialize_flow_system(start, periods, freq)

                    if success:
                        st.sidebar.success("Configuration imported successfully")
                        st.rerun()
                    else:
                        st.sidebar.error(message)
            else:
                st.sidebar.error("Invalid configuration file structure")
        except Exception as e:
            st.sidebar.error(f"Error importing system: {str(e)}")