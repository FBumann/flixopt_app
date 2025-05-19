import streamlit as st

def delete_component(name: str):
    """Delete a converter from the system"""
    try:
        st.session_state.flow_system.components.pop(name)
        return True
    except Exception as e:
        st.error(f"Error deleting converter: {str(e)}")
        return False