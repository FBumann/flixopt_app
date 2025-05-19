import streamlit as st
import flixopt as fx
import numpy as np

from utils.session_state import add_element, delete_element
from .flows import create_flow_ui

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
    class_name = "Source"
    st.title(f"Create {class_name}")

    # Create a container for the source UI
    source_container = st.container()

    with source_container:
        # LAYER 1: Basic Source Information
        st.subheader("Basic Source Information")
        source_name = st.text_input("Source Name", value="NewSource", key="source_name")
        st.info("A Source is a component that generates energy or material and outputs it to a bus.")

        # Use the modular Flow UI (passing the source name to suggest flow name)
        flow_params = create_flow_ui(
            prefix="source_flow",
            default_name="source",
            description="Configure the output flow from this source"
        )

        # Create button
        if st.button("Create Source", key="create_source"):
            try:
                # Handle on_off_parameters separately (needs class instance)
                on_off_params = None
                if "on_off_parameters" in flow_params:
                    on_off_params = flow_params.pop("on_off_parameters")
                    if on_off_params:
                        # You'll need to adjust this to match your fx.OnOffParameters class
                        flow_params["on_off_parameters"] = fx.OnOffParameters(**on_off_params)

                # Create the Source object
                source = fx.Source(
                    label=source_name,
                    source=fx.Flow(**flow_params),
                )

                add_element(source, 'sources')

                # Display success message
                st.success(f"Successfully created Source '{source_name}' with Flow '{flow_params['label']}'")

                # Display representation of the created objects
                with st.expander("Created Source Details", expanded=True):
                    st.write("##### Source")
                    st.json(source.to_json())

            except Exception as e:
                st.error(f"Error creating Source: {str(e)}")

def create_sink_ui():
    class_name = "Sink"
    st.title(f"Create {class_name}")

    # Create a container for the sink UI
    sink_container = st.container()

    with sink_container:
        # Basic Sink Information
        st.subheader("Basic Sink Information")
        sink_name = st.text_input("Sink Name", value="NewSink", key="sink_name")
        st.info("A Sink is a component that consumes energy or material from a bus.")

        # Use the modular Flow UI with a different prefix
        flow_params = create_flow_ui(
            prefix="sink_flow",
            default_name="sink",
            description="Configure the input flow to this sink"
        )

        # Create button
        if st.button("Create Sink", key="create_sink"):
            try:
                # Handle on_off_parameters separately (needs class instance)
                on_off_params = None
                if "on_off_parameters" in flow_params:
                    on_off_params = flow_params.pop("on_off_parameters")
                    if on_off_params:
                        flow_params["on_off_parameters"] = fx.OnOffParameters(**on_off_params)

                # Create the Sink object (assuming similar structure to Source)
                sink = fx.Sink(
                    label=sink_name,
                    sink=fx.Flow(**flow_params),
                )

                # Display success message
                st.success(f"Successfully created Sink '{sink_name}' with Flow '{flow_params['label']}'")

                # Store in session state
                if "sinks" not in st.session_state:
                    st.session_state.sinks = {}

                st.session_state.sinks[sink_name] = sink

                # Display representation
                with st.expander("Created Sink Details", expanded=True):
                    st.write("##### Sink")
                    st.write(f"Label: {sink.label}")
                    st.write(f"Inputs: {[i.label for i in sink.inputs]}")
                    if "meta_data" in flow_params:
                        st.write(f"Meta Data: {flow_params['meta_data']}")

                    st.write("##### Flow")
                    for key, value in flow_params.items():
                        if key not in ["meta_data"]:
                            if isinstance(value, (np.ndarray, list)):
                                st.write(f"{key}: Array with {len(value)} values")
                            else:
                                st.write(f"{key}: {value}")

                    if on_off_params:
                        st.write("on_off_parameters:")
                        for k, v in on_off_params.items():
                            st.write(f"  {k}: {v}")

            except Exception as e:
                st.error(f"Error creating Sink: {str(e)}")

def display_existing_sources_sinks():
    """Display the list of existing sources and sinks"""
    col1, col2 = st.columns(2)

    with col1:
        if st.session_state.elements['sources']:
            st.write("Current Sources:")

            # Create a table of sources with options to delete
            for i, source in enumerate(st.session_state.elements['sources']):
                cols = st.columns([3, 1])
                cols[0].write(f"{i+1}. {source}")

                if cols[1].button("Delete", key=f"delete_source_{source}"):
                    delete_element(source, 'sources')
                    st.rerun()

    with col2:
        if st.session_state.elements['sinks']:
            st.write("Current Sinks:")

            # Create a table of sinks with options to delete
            for i, sink in enumerate(st.session_state.elements['sinks']):
                cols = st.columns([3, 1])
                cols[0].write(f"{i+1}. {sink}")

                if cols[1].button("Delete", key=f"delete_sink_{i}"):
                    delete_element(sink, 'sinks')
                    st.rerun()
