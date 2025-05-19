import streamlit as st

def render_help_page():
    """Render the Help & Documentation page"""
    st.title("Help & Documentation")

    # Documentation tabs
    doc_tabs = st.tabs(["Getting Started", "Component Guide", "Optimization Tips", "API Reference"])

    with doc_tabs[0]:
        render_getting_started()

    with doc_tabs[1]:
        render_component_guide()

    with doc_tabs[2]:
        render_optimization_tips()

    with doc_tabs[3]:
        render_api_reference()

def render_getting_started():
    """Render the Getting Started documentation"""
    st.header("Getting Started with FlixOpt")
    st.markdown("""
        ## Welcome to the FlixOpt Energy System Modeler

        This application allows you to create, configure, and solve energy system models using the FlixOpt framework.

        ### Basic Workflow

        1. **Configure your system**: Set the time range and basic parameters
        2. **Add components**: Define buses, effects, converters, storage systems, sources, and sinks
        3. **Run optimization**: Set solver parameters and optimize the system
        4. **Analyze results**: Visualize and export optimization results

        ### Quick Start Guide

        The fastest way to get started is to use one of the provided example templates:

        1. Go to the "Example Templates" section from the sidebar
        2. Choose a template that matches your modeling needs
        3. Click "Load Selected Template" to populate the model
        4. Switch back to "Model Builder" to customize and run the model

        ### Video Tutorial

        Watch this introductory video to learn the basics of energy system modeling with FlixOpt:
        """)

    st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")  # Replace with actual tutorial video

def render_component_guide():
    """Render the Component Guide documentation"""
    st.header("Component Guide")
    st.markdown("""
        ## Understanding FlixOpt Components

        The FlixOpt framework models energy systems as a network of interconnected components.
        Here's what each component type represents:

        ### Buses

        Buses represent energy carriers (electricity, heat, gas, etc.) and enforce energy balance constraints.
        All energy flows into and out of a bus must balance at each time step.

        **Example**: An electricity bus connects generators (inputs) with consumers (outputs).

        ### Effects

        Effects quantify the impact of system operation, such as costs, CO₂ emissions, or primary energy consumption.
        Effects can be defined as objectives (to minimize/maximize) or as constraints.

        **Example**: A "costs" effect tracks monetary expenses across all components.

        ### Converters

        Converters transform energy from one form to another, with defined efficiencies and capacities.

        **Examples**:
        - **Boiler**: Converts gas to heat
        - **CHP (Combined Heat and Power)**: Converts fuel to both electricity and heat
        - **Heat Pump**: Converts electricity to heat (with a COP > 1)

        ### Storage Systems

        Storage components allow energy to be stored and released over time, enabling temporal flexibility.

        **Example**: A thermal storage tank stores heat for later use, with charging/discharging efficiencies.

        ### Sources and Sinks

        Sources introduce energy into the system, while sinks consume energy.

        **Examples**:
        - **Sources**: Gas supply, grid electricity, renewable generation
        - **Sinks**: Heat demand, electricity consumption, grid feed-in
        """)

    # Component diagram
    st.image("https://via.placeholder.com/800x400?text=FlixOpt+Component+Overview")

def render_optimization_tips():
    """Render the Optimization Tips documentation"""
    st.header("Optimization Tips")
    st.markdown("""
        ## Best Practices for Energy System Optimization

        Follow these guidelines to create effective and solvable models:

        ### 1. Start Simple

        Begin with a minimal system and gradually add complexity. This makes it easier to identify and fix issues.

        ### 2. Verify Component Connections

        Ensure all components are properly connected through buses. Missing connections are a common source of errors.

        ### 3. Set Appropriate Constraints

        - **Too tight constraints** may make the problem infeasible
        - **Too loose constraints** may lead to unrealistic solutions
        - **Balance constraints** to reflect real-world limitations while allowing optimization flexibility

        ### 4. Scale Parameters Appropriately

        Use consistent units and scales for all parameters to avoid numerical issues:

        - **Energy flows**: Typically in kW
        - **Capacities**: Typically in kWh or kW
        - **Costs**: Choose a consistent monetary unit (€, $, etc.)

        ### 5. Solver Settings

        - **Relative Gap**: 0.01 (1%) is a good starting point for most models
        - **Time Limit**: Start with 60 seconds, increase for complex models
        - **Consider Relaxations**: If the model is infeasible, try relaxing some constraints

        ### 6. Debugging Strategies

        If your optimization fails or produces unexpected results:

        1. **Check for infeasibility**: Look for conflicting constraints
        2. **Examine bounds**: Ensure min/max values are realistic
        3. **Simplify**: Temporarily remove components to isolate issues
        4. **Validate inputs**: Verify all input data and profiles
        """)

def render_api_reference():
    """Render the API Reference documentation"""
    st.header("API Reference")
    st.markdown("""
        ## FlixOpt Framework Reference

        This web app is built on the FlixOpt Python framework. For full API documentation, visit the official documentation.

        ### Core Classes

        ```python
        # System definition
        fx.FlowSystem(timesteps)

        # Energy carriers
        fx.Bus(label, excess_penalty_per_flow_hour=value)

        # Effects (objectives and constraints)
        fx.Effect(label, unit, description, is_standard=bool, is_objective=bool)

        # Converters
        fx.linear_converters.Boiler(label, eta, Q_th, Q_fu)
        fx.linear_converters.CHP(label, eta_el, eta_th, P_el, Q_th, Q_fu)

        # Storage
        fx.Storage(label, charging, discharging, capacity_in_flow_hours)

        # Sources and sinks
        fx.Source(label, source=flow)
        fx.Sink(label, sink=flow)

        # Flows
        fx.Flow(label, bus, size, effects_per_flow_hour={})
        ```

        ### Investment Parameters

        ```python
        fx.InvestParameters(fixed_size, minimum_size, maximum_size, fix_effects, specific_effects)
        ```

        ### On/Off Parameters

        ```python
        fx.OnOffParameters(
            on_hours_total_min, on_hours_total_max,
            consecutive_on_hours_min, consecutive_on_hours_max,
            consecutive_off_hours_min, consecutive_off_hours_max,
            effects_per_switch_on, effects_per_running_hour
        )
        ```

        ### Results Analysis

        ```python
        # Access results
        results = calculation.results

        # Component results
        component_results = results[component_label]

        # Flow results
        flow_rates = results.get_timeseries(f"{component_label}({flow_label})|flow_rate")

        # Effect results
        total_effect = results.get_total_effect(effect_label)
        component_effect = results.get_total_effect_for_component(effect_label, component_label)
        ```
        """)

    st.markdown("""
        For more detailed documentation and examples, refer to the [FlixOpt Documentation](https://example.com/flixopt/docs).
        """)