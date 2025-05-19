import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import tempfile
import os
import zipfile
import io
import json

def render_results_tab():
    """Render the Results tab UI"""
    st.header("Results Visualization")

    if st.session_state.results is None:
        st.warning("Please run the optimization first to see results.")
        return

    results = st.session_state.results

    # Key Performance Indicators
    st.subheader("Key Performance Indicators")

    # Extract objective values
    objective_effects = [effect for effect in st.session_state.elements['effects'] if effect.is_objective]
    if objective_effects:
        objective_values = {}
        for effect in objective_effects:
            try:
                # Get total effect value
                value = results.get_total_effect(effect.label)
                objective_values[effect.label] = value
            except:
                objective_values[effect.label] = "N/A"

        # Display in columns
        cols = st.columns(len(objective_values))
        for i, (label, value) in enumerate(objective_values.items()):
            with cols[i]:
                st.metric(f"Total {label}", f"{value:.2f}" if isinstance(value, (int, float)) else value)

    # Results visualization options
    st.subheader("Visualization")

    # Component selection for visualization
    component_types = ["Buses", "Converters", "Storage", "System Overview"]
    viz_type = st.selectbox("Component Type", component_types)

    if viz_type == "Buses":
        render_bus_visualization(results)
    elif viz_type == "Converters":
        render_converter_visualization(results)
    elif viz_type == "Storage":
        render_storage_visualization(results)
    elif viz_type == "System Overview":
        render_system_visualization(results)

    # Export results section
    render_export_section(results)

def render_bus_visualization(results):
    """Render visualization for buses"""
    # Bus balance visualization
    if st.session_state.elements['buses']:
        selected_bus = st.selectbox(
            "Select Bus",
            list(st.session_state.flow_system.buses)
        )

        # Visualization type for buses
        bus_viz_type = st.radio(
            "Visualization Type",
            ["Node Balance", "Node Balance (Pie Chart)", "Flow Rates Heatmap"]
        )

        try:
            if bus_viz_type == "Node Balance":
                # Create a placeholder for the matplotlib figure
                fig_placeholder = st.empty()

                # Generate the plot
                fig, ax = plt.subplots(figsize=(10, 6))
                results[selected_bus].plot_node_balance(ax=ax)

                # Display the plot
                fig_placeholder.pyplot(fig)

            elif bus_viz_type == "Node Balance (Pie Chart)":
                # Create a placeholder for the matplotlib figure
                fig_placeholder = st.empty()

                # Generate the plot
                fig, ax = plt.subplots(figsize=(10, 6))
                results[selected_bus].plot_node_balance_pie(ax=ax)

                # Display the plot
                fig_placeholder.pyplot(fig)

            elif bus_viz_type == "Flow Rates Heatmap":
                # Get flows for the selected bus
                component_flows = []
                for component_type in ['converters', 'storages', 'sources', 'sinks']:
                    for component in st.session_state.elements[component_type]:
                        for flow in component.flow:
                            if hasattr(flow, 'bus') and flow.bus == selected_bus:
                                component_flows.append(
                                    f"{component.label}({flow.label})|flow_rate"
                                )

                if component_flows:
                    selected_flow = st.selectbox("Select Flow", component_flows)

                    # Create a placeholder for the matplotlib figure
                    fig_placeholder = st.empty()

                    # Generate the plot
                    fig, ax = plt.subplots(figsize=(10, 6))
                    results.plot_heatmap(selected_flow, ax=ax)

                    # Display the plot
                    fig_placeholder.pyplot(fig)
                else:
                    st.warning(f"No flows found for bus {selected_bus}")
        except Exception as e:
            st.error(f"Error generating visualization: {str(e)}")
    else:
        st.warning("No buses available for visualization.")

def render_converter_visualization(results):
    """Render visualization for converters"""
    # Converter visualization
    if st.session_state.elements['converters']:
        converter_options = [
            conv.label for conv in st.session_state.elements['converters']
        ]
        selected_converter = st.selectbox("Select Converter", converter_options)

        # Visualization type for converters
        converter_viz_type = st.radio(
            "Visualization Type",
            ["Node Balance", "Flow Rates Heatmap"]
        )

        try:
            if converter_viz_type == "Node Balance":
                # Create a placeholder for the matplotlib figure
                fig_placeholder = st.empty()

                # Generate the plot
                fig, ax = plt.subplots(figsize=(10, 6))
                results[selected_converter].plot_node_balance(ax=ax)

                # Display the plot
                fig_placeholder.pyplot(fig)

            elif converter_viz_type == "Flow Rates Heatmap":
                # Get converter flows
                converter = next(
                    (c for c in st.session_state.elements['converters']
                     if c.label == selected_converter),
                    None
                )
                if converter:
                    flow_options = [
                        f"{selected_converter}({flow.label})|flow_rate"
                        for flow in converter.flow
                    ]

                    if flow_options:
                        selected_flow = st.selectbox("Select Flow", flow_options)

                        # Create a placeholder for the matplotlib figure
                        fig_placeholder = st.empty()

                        # Generate the plot
                        fig, ax = plt.subplots(figsize=(10, 6))
                        results.plot_heatmap(selected_flow, ax=ax)

                        # Display the plot
                        fig_placeholder.pyplot(fig)
                    else:
                        st.warning(f"No flows found for converter {selected_converter}")
        except Exception as e:
            st.error(f"Error generating visualization: {str(e)}")
    else:
        st.warning("No converters available for visualization.")

def render_storage_visualization(results):
    """Render visualization for storage systems"""
    # Storage visualization
    if st.session_state.elements['storages']:
        storage_options = [
            storage.label for storage in st.session_state.elements['storages']
        ]
        selected_storage = st.selectbox("Select Storage", storage_options)

        try:
            # Create a placeholder for the matplotlib figure
            fig_placeholder = st.empty()

            # Generate charge state plot
            fig, ax = plt.subplots(figsize=(10, 6))
            results[selected_storage].plot_charge_state(ax=ax)

            # Display the plot
            fig_placeholder.pyplot(fig)

            # Show additional storage metrics
            try:
                storage = next(
                    (s for s in st.session_state.elements['storages']
                     if s.label == selected_storage),
                    None
                )
                if storage:
                    # Calculate storage utilization metrics
                    charge_state = results[selected_storage].charge_state
                    if charge_state is not None:
                        max_charge = charge_state.max()
                        avg_charge = charge_state.mean()
                        utilization = avg_charge / max_charge if max_charge > 0 else 0

                        # Display metrics in columns
                        cols = st.columns(3)
                        with cols[0]:
                            st.metric("Maximum Charge", f"{max_charge:.2f} kWh")
                        with cols[1]:
                            st.metric("Average Charge", f"{avg_charge:.2f} kWh")
                        with cols[2]:
                            st.metric("Utilization Factor", f"{utilization:.2%}")
            except Exception as e:
                st.warning(f"Could not calculate storage metrics: {str(e)}")
        except Exception as e:
            st.error(f"Error generating visualization: {str(e)}")
    else:
        st.warning("No storage systems available for visualization.")

def render_system_visualization(results):
    """Render system-wide visualization"""
    st.subheader("Energy Balance by Component Type")

    try:
        # Calculate total energy input/output by component type
        component_energy = {}

        # Process converters
        for converter in st.session_state.elements['converters']:
            component_energy[converter.label] = 0
            for flow in converter.flow:
                if hasattr(flow, 'is_input') and flow.is_input:
                    # Input flow (negative)
                    flow_rates = results[converter.label][flow.label].flow_rate
                    if flow_rates is not None:
                        component_energy[converter.label] -= flow_rates.sum()
                else:
                    # Output flow (positive)
                    flow_rates = results[converter.label][flow.label].flow_rate
                    if flow_rates is not None:
                        component_energy[converter.label] += flow_rates.sum()

        # Process sources (always positive contribution)
        for source in st.session_state.elements['sources']:
            source_flow = source.source
            flow_rates = results[source.label][source_flow.label].flow_rate
            if flow_rates is not None:
                component_energy[source.label] = flow_rates.sum()

        # Process sinks (always negative contribution)
        for sink in st.session_state.elements['sinks']:
            sink_flow = sink.sink
            flow_rates = results[sink.label][sink_flow.label].flow_rate
            if flow_rates is not None:
                component_energy[sink.label] = -flow_rates.sum()

        # Create dataframe for plotting
        df = pd.DataFrame(
            list(component_energy.items()),
            columns=['Component', 'Net Energy']
        )

        df['Type'] = df['Component'].apply(
            lambda x: next(
                (k for k, v in st.session_state.elements.items()
                 if any(c.label == x for c in v)),
                'Other'
            )
        )

        # Simplify component types for display
        type_mapping = {
            'converters': 'Converter',
            'storages': 'Storage',
            'sources': 'Source',
            'sinks': 'Sink'
        }
        df['Type'] = df['Type'].map(lambda x: type_mapping.get(x, x.capitalize()))

        # Create the bar chart
        fig = px.bar(
            df,
            x='Component',
            y='Net Energy',
            color='Type',
            title='System-wide Energy Balance',
            labels={'Net Energy': 'Net Energy (kWh)', 'Component': 'Component'}
        )
        st.plotly_chart(fig, use_container_width=True)

        # Effects distribution
        st.subheader("Effects Distribution")

        # Calculate effects by component
        effect_data = []

        # Loop through effect types
        for effect in st.session_state.elements['effects']:
            effect_label = effect.label

            # Process all components for this effect
            for component_type in ['converters', 'storages', 'sources', 'sinks']:
                for component in st.session_state.elements[component_type]:
                    component_label = component.label
                    component_type_label = type_mapping.get(
                        component_type,
                        component_type.capitalize()
                    )

                    # Try to get total effect for this component
                    try:
                        effect_value = results.get_total_effect_for_component(
                            effect_label,
                            component_label
                        )
                        effect_data.append({
                            'Effect': effect_label,
                            'Component': component_label,
                            'Type': component_type_label,
                            'Value': effect_value
                        })
                    except:
                        # Effect not applicable for this component
                        pass

        # Create dataframe for plotting effects
        if effect_data:
            effect_df = pd.DataFrame(effect_data)

            # Select effect to display
            effect_options = effect_df['Effect'].unique()
            selected_effect = st.selectbox("Select Effect", effect_options)

            # Filter dataframe for selected effect
            filtered_df = effect_df[effect_df['Effect'] == selected_effect]

            # Create the bar chart for effects
            fig = px.bar(
                filtered_df,
                x='Component',
                y='Value',
                color='Type',
                title=f'{selected_effect} Distribution by Component',
                labels={
                    'Value': f"{selected_effect} ({next((e.unit for e in st.session_state.elements['effects'] if e.label == selected_effect), '')})"
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating system overview: {str(e)}")

def render_export_section(results):
    """Render the export results section"""
    st.subheader("Export Results")

    export_format = st.selectbox(
        "Export Format",
        ["CSV", "Excel", "JSON"]
    )

    export_content = st.multiselect(
        "Export Content",
        ["Flow Rates", "Effects", "Storage States", "All"]
    )

    if st.button("Export Results"):
        try:
            with st.spinner("Preparing export..."):
                # Create a temporary directory to store export files
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Determine which data to export
                    export_flow_rates = "Flow Rates" in export_content or "All" in export_content
                    export_effects = "Effects" in export_content or "All" in export_content
                    export_storage = "Storage States" in export_content or "All" in export_content

                    files_to_export = []

                    # Export flow rates
                    if export_flow_rates:
                        flow_rates_data = {}

                        # Collect flow rates from all components
                        for component_type in ['converters', 'storages', 'sources', 'sinks']:
                            for component in st.session_state.elements[component_type]:
                                for flow in component.flow:
                                    flow_key = f"{component.label}({flow.label})|flow_rate"
                                    try:
                                        flow_rates = results.get_timeseries(flow_key)
                                        if flow_rates is not None:
                                            flow_rates_data[flow_key] = flow_rates
                                    except:
                                        pass

                        # Convert to dataframe
                        if flow_rates_data:
                            flow_df = pd.DataFrame(
                                flow_rates_data,
                                index=st.session_state.timesteps
                            )

                            # Export based on selected format
                            if export_format == "CSV":
                                file_path = os.path.join(temp_dir, "flow_rates.csv")
                                flow_df.to_csv(file_path)
                                files_to_export.append(file_path)
                            elif export_format == "Excel":
                                file_path = os.path.join(temp_dir, "flow_rates.xlsx")
                                flow_df.to_excel(file_path, sheet_name="Flow Rates")
                                files_to_export.append(file_path)
                            elif export_format == "JSON":
                                file_path = os.path.join(temp_dir, "flow_rates.json")
                                flow_df.to_json(file_path)
                                files_to_export.append(file_path)

                    # Export effects
                    if export_effects:
                        # Collect total effects for all components
                        effects_data = {}

                        for effect in st.session_state.elements['effects']:
                            effect_label = effect.label
                            effects_data[effect_label] = {}

                            for component_type in ['converters', 'storages', 'sources', 'sinks']:
                                for component in st.session_state.elements[component_type]:
                                    try:
                                        effect_value = results.get_total_effect_for_component(
                                            effect_label, component.label
                                        )
                                        effects_data[effect_label][component.label] = effect_value
                                    except:
                                        pass

                        # Convert to dataframe
                        effects_df = pd.DataFrame()
                        for effect, components in effects_data.items():
                            effect_df = pd.DataFrame(
                                list(components.items()),
                                columns=['Component', effect]
                            )

                            if effects_df.empty:
                                effects_df = effect_df
                            else:
                                effects_df = effects_df.merge(
                                    effect_df, on='Component', how='outer'
                                )

                        # Export based on selected format
                        if not effects_df.empty:
                            if export_format == "CSV":
                                file_path = os.path.join(temp_dir, "effects.csv")
                                effects_df.to_csv(file_path, index=False)
                                files_to_export.append(file_path)
                            elif export_format == "Excel":
                                file_path = os.path.join(temp_dir, "effects.xlsx")
                                effects_df.to_excel(file_path, sheet_name="Effects", index=False)
                                files_to_export.append(file_path)
                            elif export_format == "JSON":
                                file_path = os.path.join(temp_dir, "effects.json")
                                effects_df.to_json(file_path, orient="records")
                                files_to_export.append(file_path)

                    # Export storage states
                    if export_storage and st.session_state.elements['storages']:
                        storage_data = {}

                        # Collect charge states for all storage components
                        for storage in st.session_state.elements['storages']:
                            try:
                                charge_state = results[storage.label].charge_state
                                if charge_state is not None:
                                    storage_data[f"{storage.label}_charge"] = charge_state
                            except:
                                pass

                        # Convert to dataframe
                        if storage_data:
                            storage_df = pd.DataFrame(
                                storage_data,
                                index=st.session_state.timesteps
                            )

                            # Export based on selected format
                            if export_format == "CSV":
                                file_path = os.path.join(temp_dir, "storage_states.csv")
                                storage_df.to_csv(file_path)
                                files_to_export.append(file_path)
                            elif export_format == "Excel":
                                file_path = os.path.join(temp_dir, "storage_states.xlsx")
                                storage_df.to_excel(file_path, sheet_name="Storage States")
                                files_to_export.append(file_path)
                            elif export_format == "JSON":
                                file_path = os.path.join(temp_dir, "storage_states.json")
                                storage_df.to_json(file_path)
                                files_to_export.append(file_path)

                    # Create a zip file with all exports if there are multiple files
                    if len(files_to_export) > 0:
                        if len(files_to_export) == 1 and export_format != "CSV":
                            # Single file download
                            file_path = files_to_export[0]
                            with open(file_path, "rb") as f:
                                file_bytes = f.read()

                            # Get filename from path
                            filename = os.path.basename(file_path)

                            # Provide download button
                            st.download_button(
                                label="Download Results",
                                data=file_bytes,
                                file_name=filename,
                                mime=f"application/{export_format.lower()}"
                            )
                        else:
                            # Multiple files or CSV - create a zip archive
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                                for file_path in files_to_export:
                                    # Get filename from path
                                    filename = os.path.basename(file_path)
                                    zip_file.write(file_path, arcname=filename)

                            # Provide download button for zip file
                            st.download_button(
                                label="Download Results (ZIP)",
                                data=zip_buffer.getvalue(),
                                file_name="flixopt_results.zip",
                                mime="application/zip"
                            )
                    else:
                        st.warning("No data to export.")
        except Exception as e:
            st.error(f"Error exporting results: {str(e)}")

    # Save model section
    st.subheader("Save Model Configuration")
    model_name = st.text_input("Model Name", "my_flixopt_model")

    if st.button("Save Model Configuration"):
        try:
            with st.spinner("Saving model configuration..."):
                # Create a dictionary representation of the model
                model_config = {
                    "name": model_name,
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

                        # Add component-specific attributes
                        if component_type == "converters":
                            if hasattr(component, "eta") and component.eta is not None:
                                component_config["eta"] = component.eta
                            if hasattr(component, "eta_el") and component.eta_el is not None:
                                component_config["eta_el"] = component.eta_el
                            if hasattr(component, "eta_th") and component.eta_th is not None:
                                component_config["eta_th"] = component.eta_th

                        # Add flows
                        if hasattr(component, "flow"):
                            component_config["flows"] = []

                            for flow in component.flow:
                                flow_config = {
                                    "label": flow.label,
                                    "size": flow.size
                                }

                                if hasattr(flow, "bus") and flow.bus is not None:
                                    flow_config["bus"] = flow.bus

                                component_config["flows"].append(flow_config)

                        # Add to components list
                        model_config["components"][component_type].append(component_config)

                # Convert to JSON
                model_json = json.dumps(model_config, indent=2)

                # Provide download button
                st.download_button(
                    label="Download Model Configuration",
                    data=model_json,
                    file_name=f"{model_name}.json",
                    mime="application/json"
                )
        except Exception as e:
            st.error(f"Error saving model configuration: {str(e)}")
