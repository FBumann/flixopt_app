import streamlit as st
import flixopt as fx
from utils.session_state import add_element, delete_element

def create_effect_ui():
    """UI for creating and managing effects"""
    st.subheader("Effects")
    st.write("Effects represent costs, emissions, or other impacts of the energy system.")

    with st.form("effect_form"):
        effect_name = st.text_input("Effect Name", value="costs")
        effect_unit = st.text_input("Unit", value="€")
        effect_description = st.text_input("Description", value="Kosten")

        col1, col2 = st.columns(2)
        with col1:
            is_standard = st.checkbox("Is Standard Effect", value=True)
        with col2:
            is_objective = st.checkbox("Is Objective", value=True)

        # Only show maximum total if not an objective
        if not is_objective:
            maximum_total = st.number_input("Maximum Total", value=0.0)
        else:
            maximum_total = None

        if st.form_submit_button("Add Effect"):
            if st.session_state.flow_system is None:
                st.error("Please initialize the flow system first.")
                return

            new_effect = fx.Effect(
                effect_name,
                effect_unit,
                effect_description,
                is_standard=is_standard,
                is_objective=is_objective,
                maximum_total=maximum_total
            )

            success, message = add_element(new_effect, 'effects')

            if success:
                st.success(message)
            else:
                st.error(message)

    # Display existing effects
    display_existing_effects()

def display_existing_effects():
    """Display the list of existing effects"""
    if not st.session_state.elements['effects']:
        return

    st.write("Current Effects:")

    # Create a table of effects with options to edit/delete
    cols = st.columns([2, 1, 1, 1, 1])
    cols[0].write("**Name**")
    cols[1].write("**Unit**")
    cols[2].write("**Type**")
    cols[3].write("**Max Total**")
    cols[4].write("**Actions**")

    for i, effect in enumerate(st.session_state.flow_system.effects.effects.values()):
        cols = st.columns([2, 1, 1, 1, 1])
        cols[0].write(effect.label_full)
        cols[1].write(effect.unit)
        cols[2].write("Objective" if effect.is_objective else "Constraint")

        # Max total (if constraint)
        if effect.is_objective:
            cols[3].write("N/A")
        else:
            cols[3].write(f"{effect.maximum_total}")

        # Action buttons
        if cols[4].button("Delete", key=f"delete_effect_{effect.label_full}"):
            delete_element(effect.label_full, 'effects')
            st.rerun()
