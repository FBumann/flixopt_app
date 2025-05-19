import streamlit as st
import pandas as pd
import flixopt as fx

def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if 'flow_system' not in st.session_state:
        st.session_state.flow_system = None

    if 'components' not in st.session_state:
        st.session_state.components = {
            'buses': [],
            'effects': [],
            'converters': [],
            'storages': [],
            'sources': [],
            'sinks': []
        }

    if 'timesteps' not in st.session_state:
        st.session_state.timesteps = None

    if 'calculation_results' not in st.session_state:
        st.session_state.calculation_results = None

    if 'template_loaded' not in st.session_state:
        st.session_state.template_loaded = None

def initialize_flow_system(start_date, periods, freq, excess_penalty=None):
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
    st.session_state.components = {
        'buses': [],
        'effects': [],
        'converters': [],
        'storages': [],
        'sources': [],
        'sinks': []
    }
    st.session_state.timesteps = None
    st.session_state.calculation_results = None

def add_component(component, component_type):
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
        st.session_state.components[component_type].append(component)
        st.session_state.flow_system.add_elements(component)
        return True, f"{component.label} added successfully!"
    except Exception as e:
        return False, f"Error adding component: {str(e)}"

def get_component_counts():
    """Get counts of components by type"""
    return {k: len(v) for k, v in st.session_state.components.items()}

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
        for effect in st.session_state.components['effects']
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
        for bus in st.session_state.components['buses']
    }

    # Count connections to each bus
    for component_type in ['converters', 'storages', 'sources', 'sinks']:
        for component in st.session_state.components[component_type]:
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