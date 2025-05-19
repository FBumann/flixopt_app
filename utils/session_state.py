import streamlit as st
import pandas as pd
import datetime
import json
import flixopt as fx


def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if 'flow_system' not in st.session_state:
        st.session_state.flow_system = None

    if 'elements' not in st.session_state:
        st.session_state.elements = {
            'buses': [],
            'effects': [],
            'converters': [],
            'storages': [],
            'sources': [],
            'sinks': []
        }

    if 'timesteps' not in st.session_state:
        st.session_state.timesteps = None

    if 'results' not in st.session_state:
        st.session_state.results = None

    if 'template_loaded' not in st.session_state:
        st.session_state.template_loaded = None

def initialize_flow_system(start_date, periods, freq):
    """
    Initialize a new flow system with given parameters.

    Parameters:
    -----------
    start_date : datetime.date
        Start date for the simulation
    periods : int
        Number of time periods
    freq : str
        Frequency string (e.g. 'h', '30min', '15min', 'd')
    excess_penalty : float, optional
        Default excess penalty for the system

    Returns:
    --------
    bool
        Success status
    str
        Success or error message
    """
    try:
        # Create time range
        timesteps = pd.date_range(start_date, periods=periods, freq=freq)
        st.session_state.timesteps = timesteps

        # Create flow system
        st.session_state.flow_system = fx.FlowSystem(timesteps)

        return True, f"Flow system initialized with {len(timesteps)} time steps from {timesteps[0]} to {timesteps[-1]}"
    except Exception as e:
        return False, f"Error initializing flow system: {str(e)}"

def reset_system():
    """Reset the entire system"""
    st.session_state.flow_system = None
    st.session_state.elements = {
        'buses': [],
        'effects': [],
        'converters': [],
        'storages': [],
        'sources': [],
        'sinks': []
    }
    st.session_state.timesteps = None
    st.session_state.results = None

def add_element(element, element_type: str):
    """
    Add a component to the system

    Parameters:
    -----------
    component : fx.Component
        FlixOpt component to add
    component_type : str
        Type of component ('buses', 'effects', etc.)

    Returns:
    --------
    bool
        Success status
    str
        Success or error message
    """
    try:
        st.session_state.flow_system.add_elements(element)
        st.session_state.elements[element_type].append(element.label_full)
        render_system_status()
        return True, f"{element.label_full} added successfully!"
    except Exception as e:
        return False, f"Error adding element: {str(e)}"

def delete_element(name: str, element_type: str):
    """Delete a component from the system"""
    try:
        # Remove from flow_system dicts
        if element_type == 'effects':
            if name in st.session_state.flow_system.effects:
                st.session_state.flow_system.effects.effects.pop(name)
            else:
                raise KeyError(f"{name} not found in flow_system.effects")
        elif element_type == 'buses':
            if name in st.session_state.flow_system.buses:
                st.session_state.flow_system.buses.pop(name)
            else:
                raise KeyError(f"{name} not found in flow_system.buses")
        else:
            if name in st.session_state.flow_system.components:
                st.session_state.flow_system.components.pop(name)
            else:
                raise KeyError(f"{name} not found in flow_system.components")

        # Remove from session_state.elements list
        if name in st.session_state.elements.get(element_type, []):
            st.session_state.elements[element_type].remove(name)
        else:
            raise ValueError(f"{name} not found in elements[{element_type}]")

        render_system_status()
    except Exception as e:
        raise Exception(f"Error deleting component: {str(e)}")


def get_component_counts():
    """Get counts of components by type"""
    return {k: len(v) for k, v in st.session_state.elements.items()}

def validate_system():
    """
    Validate the system configuration

    Returns:
    --------
    bool
        Whether the system passes validation
    list
        List of validation issues
    """
    validation_issues = []

    # Skip validation if system not initialized
    if st.session_state.flow_system is None:
        validation_issues.append("System not initialized")
        return False, validation_issues

    # Count components by type
    component_counts = get_component_counts()

    # Check for basic requirements
    if component_counts['buses'] == 0:
        validation_issues.append("No energy buses defined")

    if component_counts['effects'] == 0:
        validation_issues.append("No effects (objectives/constraints) defined")

    objective_defined = any(
        effect.is_objective
        for effect in st.session_state.elements['effects']
    )
    if not objective_defined and component_counts['effects'] > 0:
        validation_issues.append("No objective function defined")

    if (component_counts['converters'] +
        component_counts['sources'] +
        component_counts['sinks']) == 0:
        validation_issues.append("No energy producers or consumers defined")

    # Check for bus connections
    bus_connections = {
        bus.label: {'in': 0, 'out': 0}
        for bus in st.session_state.elements['buses']
    }

    # Count connections to each bus
    for component_type in ['converters', 'storages', 'sources', 'sinks']:
        for component in st.session_state.elements[component_type]:
            if hasattr(component, 'flow'):
                for flow in component.flow:
                    if hasattr(flow, 'bus') and flow.bus in bus_connections:
                        # Determine flow direction
                        if (component_type == 'sources') or \
                                (component_type == 'converters' and not hasattr(flow, 'is_input')):
                            bus_connections[flow.bus]['in'] += 1
                        elif (component_type == 'sinks') or \
                                (component_type == 'converters' and hasattr(flow, 'is_input') and flow.is_input):
                            bus_connections[flow.bus]['out'] += 1

    # Check for disconnected buses
    for bus, connections in bus_connections.items():
        if connections['in'] == 0:
            validation_issues.append(f"Bus '{bus}' has no input connections")
        if connections['out'] == 0:
            validation_issues.append(f"Bus '{bus}' has no output connections")

    return len(validation_issues) == 0, validation_issues

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
                for component_type, components in st.session_state.elements.items():
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