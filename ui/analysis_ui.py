import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def render_analysis_tab():
    """Render the Advanced Analysis tab"""
    st.header("Advanced Analysis")

    # Check if results are available
    if st.session_state.calculation_results is None:
        st.warning("Please run the optimization first to perform advanced analysis.")
        return

    analysis_type = st.selectbox(
        "Analysis Type",
        [
            "Sensitivity Analysis",
            "Load Duration Curves",
            "Energy Flows Sankey Diagram",
            "Component Utilization",
            "Emissions Analysis",
            "Cost Breakdown"
        ]
    )

    if analysis_type == "Sensitivity Analysis":
        render_sensitivity_analysis()
    elif analysis_type == "Load Duration Curves":
        render_load_duration_curves()
    elif analysis_type == "Energy Flows Sankey Diagram":
        render_sankey_diagram()
    elif analysis_type == "Component Utilization":
        render_component_utilization()
    elif analysis_type == "Emissions Analysis":
        render_emissions_analysis()
    elif analysis_type == "Cost Breakdown":
        render_cost_breakdown()

def render_sensitivity_analysis():
    """Render sensitivity analysis UI"""
    st.subheader("Sensitivity Analysis")
    st.write("This analysis shows how changing key parameters affects optimization results.")

    # Placeholder for future implementation
    st.info("Sensitivity analysis implementation is planned for a future version.")

    # Conceptual design
    st.write("""
    In a full implementation, this section would allow you to:
    1. Select a parameter to vary (e.g., component efficiency, energy prices)
    2. Define a range of values to test
    3. Run multiple optimizations automatically
    4. Visualize how objective values and component operation change
    """)

    # Example visualization
    # Create dummy data for demonstration
    param_values = [0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
    objective_values = [15000, 14200, 13500, 13000, 12700, 12500]

    fig = px.line(
        x=param_values,
        y=objective_values,
        markers=True,
        labels={"x": "Boiler Efficiency", "y": "Total System Cost (€)"},
        title="Example: Effect of Boiler Efficiency on Total Cost"
    )
    st.plotly_chart(fig, use_container_width=True)

def render_load_duration_curves():
    """Render load duration curves analysis"""
    st.subheader("Load Duration Curves")
    st.write("""
    Load duration curves show how long a system operates at different load levels, 
    sorted from highest to lowest.
    """)

    # Select bus to analyze
    if not st.session_state.components['buses']:
        st.warning("No buses available for analysis.")
        return

    selected_bus = st.selectbox(
        "Select Bus for Load Duration Analysis",
        list(st.session_state.flow_system.buses)
    )

    try:
        # Get all flows connected to this bus
        results = st.session_state.calculation_results
        flow_data = {}

        # Collect all flows from sources to this bus (positive)
        for source in st.session_state.components['sources']:
            if source.source.bus == selected_bus:
                flow_key = f"{source.label}({source.source.label})|flow_rate"
                try:
                    flow_rates = results.get_timeseries(flow_key)
                    if flow_rates is not None:
                        flow_data[source.label] = flow_rates
                except:
                    pass

        # If we have flow data, create load duration curve
        if flow_data:
            # Convert to dataframe
            df = pd.DataFrame(flow_data, index=st.session_state.timesteps)

            # Calculate total load
            df['Total'] = df.sum(axis=1)

            # Sort values in descending order for duration curve
            sorted_values = df['Total'].sort_values(ascending=False).reset_index(drop=True)

            # Create duration curve
            fig = px.line(
                sorted_values,
                labels={"index": "Hours", "value": f"Load on {selected_bus} (kW)"},
                title=f"Load Duration Curve for {selected_bus}"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Show statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Peak Load", f"{sorted_values.max():.2f} kW")
            with col2:
                st.metric("Average Load", f"{sorted_values.mean():.2f} kW")
            with col3:
                st.metric("Load Factor", f"{sorted_values.mean() / sorted_values.max():.2%}")
        else:
            st.warning(f"No flow data available for bus {selected_bus}")
    except Exception as e:
        st.error(f"Error generating load duration curve: {str(e)}")

def render_sankey_diagram():
    """Render Sankey diagram of energy flows"""
    st.subheader("Energy Flows Sankey Diagram")
    st.write("This diagram shows the overall energy flows between components in the system.")

    # Placeholder for future implementation
    st.info("Energy flow Sankey diagram implementation is planned for a future version.")

    # Conceptual design
    st.write("""
    A Sankey diagram would show:
    - Energy flows from sources to buses
    - Energy transformations in converters
    - Energy storage and retrieval
    - Energy consumption by sinks
    - Overall system efficiency
    """)

    # Example Sankey diagram with dummy data
    fig = go.Figure(data=[go.Sankey(
        node = dict(
            pad = 15,
            thickness = 20,
            line = dict(color = "black", width = 0.5),
            label = ["Gas Source", "Electricity Source", "Gas Bus", "Electricity Bus", "Heat Bus",
                     "Boiler", "CHP", "Heat Demand", "Electricity Demand"],
            color = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3", "#FF6692", "#B6E880", "#FF97FF"]
        ),
        link = dict(
            source = [0, 1, 2, 2, 3, 3, 5, 6, 6],
            target = [2, 3, 5, 6, 8, 6, 4, 4, 3],
            value = [100, 50, 70, 30, 30, 20, 65, 20, 10],
            color = ["rgba(0,0,96,0.2)", "rgba(239,85,59,0.2)", "rgba(0,204,150,0.2)",
                     "rgba(0,204,150,0.2)", "rgba(171,99,250,0.2)", "rgba(171,99,250,0.2)",
                     "rgba(25,211,243,0.2)", "rgba(255,102,146,0.2)", "rgba(255,102,146,0.2)"]
        )
    )])

    fig.update_layout(title_text="Example: System Energy Flows", font_size=12)
    st.plotly_chart(fig, use_container_width=True)

def render_component_utilization():
    """Render component utilization analysis"""
    st.subheader("Component Utilization Analysis")
    st.write("This analysis shows how efficiently different components are being utilized.")

    # Choose component type to analyze
    component_type = st.selectbox(
        "Select Component Type",
        ["Converters", "Storage Systems"],
        key="utilization_component_type"
    )

    if component_type == "Converters":
        render_converter_utilization()
    else:
        render_storage_utilization()

def render_converter_utilization():
    """Render converter utilization analysis"""
    # Check if converters exist
    if not st.session_state.components['converters']:
        st.warning("No converters available for analysis.")
        return

    results = st.session_state.calculation_results
    utilization_data = []

    # Calculate utilization for each converter
    for converter in st.session_state.components['converters']:
        # Find the primary output flow
        main_flow = None
        for flow in converter.flow:
            if not hasattr(flow, 'is_input') or not flow.is_input:
                main_flow = flow
                break

        if main_flow is not None:
            try:
                # Get flow rates
                flow_key = f"{converter.label}({main_flow.label})|flow_rate"
                flow_rates = results.get_timeseries(flow_key)

                if flow_rates is not None:
                    # Calculate utilization metrics
                    max_rate = main_flow.size
                    avg_rate = flow_rates.mean()
                    max_actual = flow_rates.max()
                    utilization = avg_rate / max_rate if max_rate > 0 else 0
                    peak_utilization = max_actual / max_rate if max_rate > 0 else 0

                    # Add to data
                    utilization_data.append({
                        'Component': converter.label,
                        'Type': type(converter).__name__,
                        'Max Capacity': max_rate,
                        'Avg Output': avg_rate,
                        'Max Actual': max_actual,
                        'Utilization': utilization,
                        'Peak Utilization': peak_utilization
                    })
            except Exception as e:
                st.warning(f"Could not calculate utilization for {converter.label}: {str(e)}")

    # Display utilization data
    if utilization_data:
        # Convert to dataframe
        df = pd.DataFrame(utilization_data)

        # Show bar chart of utilization by component
        fig = px.bar(
            df,
            x='Component',
            y=['Utilization', 'Peak Utilization'],
            barmode='group',
            labels={'value': 'Utilization Factor', 'variable': 'Metric'},
            title="Converter Utilization Analysis"
        )
        fig.update_layout(yaxis_tickformat='.0%')
        st.plotly_chart(fig, use_container_width=True)

        # Show data table
        st.write("Detailed Utilization Data")
        display_df = df.copy()
        display_df['Utilization'] = display_df['Utilization'].apply(lambda x: f"{x:.1%}")
        display_df['Peak Utilization'] = display_df['Peak Utilization'].apply(lambda x: f"{x:.1%}")
        display_df['Max Capacity'] = display_df['Max Capacity'].apply(lambda x: f"{x:.1f} kW")
        display_df['Avg Output'] = display_df['Avg Output'].apply(lambda x: f"{x:.1f} kW")
        display_df['Max Actual'] = display_df['Max Actual'].apply(lambda x: f"{x:.1f} kW")
        st.dataframe(display_df, use_container_width=True)
    else:
        st.warning("No utilization data could be calculated.")

def render_storage_utilization():
    """Render storage utilization analysis"""
    # Check if storage systems exist
    if not st.session_state.components['storages']:
        st.warning("No storage systems available for analysis.")
        return

    results = st.session_state.calculation_results
    utilization_data = []

    # Calculate utilization for each storage system
    for storage in st.session_state.components['storages']:
        try:
            # Get charge state
            charge_state = results[storage.label].charge_state

            if charge_state is not None:
                # Calculate capacity
                capacity = storage.capacity_in_flow_hours * storage.charging.size

                # Calculate utilization metrics
                max_charge = charge_state.max()
                min_charge = charge_state.min()
                avg_charge = charge_state.mean()
                utilization = avg_charge / capacity if capacity > 0 else 0
                cycling_depth = (max_charge - min_charge) / capacity if capacity > 0 else 0

                # Add to data
                utilization_data.append({
                    'Storage': storage.label,
                    'Capacity': capacity,
                    'Max Charge': max_charge,
                    'Min Charge': min_charge,
                    'Avg Charge': avg_charge,
                    'Utilization': utilization,
                    'Cycling Depth': cycling_depth
                })
        except Exception as e:
            st.warning(f"Could not calculate utilization for {storage.label}: {str(e)}")

    # Display utilization data
    if utilization_data:
        # Convert to dataframe
        df = pd.DataFrame(utilization_data)

        # Show bar chart of utilization by storage
        fig = px.bar(
            df,
            x='Storage',
            y=['Utilization', 'Cycling Depth'],
            barmode='group',
            labels={'value': 'Factor', 'variable': 'Metric'},
            title="Storage Utilization Analysis"
        )
        fig.update_layout(yaxis_tickformat='.0%')
        st.plotly_chart(fig, use_container_width=True)

        # Show data table
        st.write("Detailed Storage Utilization Data")
        display_df = df.copy()
        display_df['Utilization'] = display_df['Utilization'].apply(lambda x: f"{x:.1%}")
        display_df['Cycling Depth'] = display_df['Cycling Depth'].apply(lambda x: f"{x:.1%}")
        display_df['Capacity'] = display_df['Capacity'].apply(lambda x: f"{x:.1f} kWh")
        display_df['Max Charge'] = display_df['Max Charge'].apply(lambda x: f"{x:.1f} kWh")
        display_df['Min Charge'] = display_df['Min Charge'].apply(lambda x: f"{x:.1f} kWh")
        display_df['Avg Charge'] = display_df['Avg Charge'].apply(lambda x: f"{x:.1f} kWh")
        st.dataframe(display_df, use_container_width=True)
    else:
        st.warning("No storage utilization data could be calculated.")

def render_emissions_analysis():
    """Render emissions analysis UI"""
    st.subheader("Emissions Analysis")

    # Check if an emissions effect exists
    has_emissions = False
    emissions_effects = []

    for effect in st.session_state.components['effects']:
        if "emission" in effect.label.lower() or "co2" in effect.label.lower():
            has_emissions = True
            emissions_effects.append(effect.label)

    if not has_emissions:
        st.warning("No emissions-related effects found. Add an effect with 'emission' or 'CO2' in the name.")
        return

    # Select emissions effect to analyze
    selected_effect = st.selectbox(
        "Select Emissions Effect",
        emissions_effects
    )

    results = st.session_state.calculation_results

    try:
        # Calculate total emissions
        total_emissions = results.get_total_effect(selected_effect)

        # Calculate emissions by component
        emissions_by_component = {}

        for component_type in ['converters', 'storages', 'sources', 'sinks']:
            for component in st.session_state.components[component_type]:
                try:
                    emissions = results.get_total_effect_for_component(
                        selected_effect,
                        component.label
                    )
                    if emissions != 0:
                        emissions_by_component[component.label] = emissions
                except:
                    pass

        # Display total emissions
        st.metric(f"Total {selected_effect}", f"{total_emissions:.2f} kg")

        # Create emissions breakdown chart
        if emissions_by_component:
            # Convert to dataframe
            df = pd.DataFrame(
                list(emissions_by_component.items()),
                columns=['Component', 'Emissions']
            )

            # Sort by emissions (absolute value)
            df = df.reindex(df['Emissions'].abs().sort_values(ascending=False).index)

            # Add component type
            df['Type'] = df['Component'].apply(
                lambda x: next(
                    (type(c).__name__ for k, v in st.session_state.components.items()
                     for c in v if c.label == x),
                    'Other'
                )
            )

            # Create bar chart
            fig = px.bar(
                df,
                x='Component',
                y='Emissions',
                color='Type',
                title=f"{selected_effect} by Component",
                labels={'Emissions': f"{selected_effect} (kg)"}
            )
            st.plotly_chart(fig, use_container_width=True)

            # Show data table
            st.write("Emissions by Component")
            display_df = df.copy()
            display_df['Emissions'] = display_df['Emissions'].apply(lambda x: f"{x:.2f} kg")
            display_df['Percentage'] = df['Emissions'] / total_emissions * 100
            display_df['Percentage'] = display_df['Percentage'].apply(lambda x: f"{x:.1f}%")
            st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("No emissions data available by component.")
    except Exception as e:
        st.error(f"Error calculating emissions: {str(e)}")

def render_cost_breakdown():
    """Render cost breakdown analysis UI"""
    st.subheader("Cost Breakdown Analysis")

    # Check if a cost effect exists
    has_costs = False
    cost_effects = []

    for effect in st.session_state.components['effects']:
        if "cost" in effect.label.lower() or "euro" in effect.label.lower() or "€" in effect.label.lower():
            has_costs = True
            cost_effects.append(effect.label)

    if not has_costs:
        st.warning("No cost-related effects found. Add an effect with 'cost', 'euro', or '€' in the name.")
        return

    # Select cost effect to analyze
    selected_effect = st.selectbox(
        "Select Cost Effect",
        cost_effects
    )

    results = st.session_state.calculation_results

    try:
        # Calculate total costs
        total_costs = results.get_total_effect(selected_effect)

        # Calculate costs by component
        costs_by_component = {}

        for component_type in ['converters', 'storages', 'sources', 'sinks']:
            for component in st.session_state.components[component_type]:
                try:
                    costs = results.get_total_effect_for_component(
                        selected_effect,
                        component.label
                    )
                    if costs != 0:
                        costs_by_component[component.label] = costs
                except:
                    pass

        # Display total costs
        st.metric(f"Total {selected_effect}", f"{total_costs:.2f} €")

        # Create cost breakdown chart
        if costs_by_component:
            # Convert to dataframe
            df = pd.DataFrame(
                list(costs_by_component.items()),
                columns=['Component', 'Costs']
            )

            # Sort by costs (absolute value)
            df = df.reindex(df['Costs'].abs().sort_values(ascending=False).index)

            # Add component type
            df['Type'] = df['Component'].apply(
                lambda x: next(
                    (type(c).__name__ for k, v in st.session_state.components.items()
                     for c in v if c.label == x),
                    'Other'
                )
            )

            # Create charts
            tab1, tab2 = st.tabs(["Bar Chart", "Pie Chart"])

            with tab1:
                # Bar chart
                fig = px.bar(
                    df,
                    x='Component',
                    y='Costs',
                    color='Type',
                    title=f"{selected_effect} Breakdown by Component",
                    labels={'Costs': f"{selected_effect} (€)"}
                )
                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                # Pie chart
                fig = px.pie(
                    df,
                    values='Costs',
                    names='Component',
                    title=f"{selected_effect} Breakdown by Component"
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)

            # Show data table
            st.write("Cost Breakdown by Component")
            display_df = df.copy()
            display_df['Costs'] = display_df['Costs'].apply(lambda x: f"{x:.2f} €")
            display_df['Percentage'] = df['Costs'] / total_costs * 100
            display_df['Percentage'] = display_df['Percentage'].apply(lambda x: f"{x:.1f}%")
            st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("No cost data available by component.")
    except Exception as e:
        st.error(f"Error calculating costs: {str(e)}")
