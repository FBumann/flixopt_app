import streamlit as st
import pandas as pd
import flixopt as fx
from utils.session_state import add_element, delete_element
from ui.profile_editor import smart_numeric_input, dict_editor

def create_effect_ui(prefix="effect", default_name="NewEffect", description=None):
    """
    Creates a modular Effect configuration UI that can be reused in different components.

    Parameters:
    -----------
    prefix : str
        Prefix for session state keys to allow multiple instances
    default_name : str
        Default name for the effect
    description : str or None
        Optional description text

    Returns:
    --------
    dict
        Dictionary of effect parameters to pass to Effect constructor
    """
    effect_params = {}

    # Basic Effect Parameters
    st.header("Create Effect")
    if description:
        st.info(description)

    col1, col2 = st.columns(2)
    with col1:
        effect_name = st.text_input("Name", value=default_name, key=f"{prefix}_name")
        effect_params["label"] = effect_name
    with col2:
        is_objective = st.checkbox(
            "Is Objective",
            value=True,
            key=f"{prefix}_is_objective",
            help="True if this effect is an optimization target"
        )
        effect_params["is_objective"] = is_objective

    col1, col2 = st.columns(2)
    with col1:
        effect_unit = st.text_input("Unit", value="€", key=f"{prefix}_unit")
        effect_params["unit"] = effect_unit

    with col2:
        effect_description = st.text_input("Description", value="Costs", key=f"{prefix}_description")
        effect_params["description"] = effect_description

    # LAYER 2: Operation Limits
    with st.expander("Operation Limits", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            minimum_operation = st.number_input(
                "Minimum Operation",
                value=None,
                key=f"{prefix}_minimum_operation",
                help="Minimal sum (only operation) of the effect"
            )
            if minimum_operation is not None:
                effect_params["minimum_operation"] = minimum_operation

        with col2:
            maximum_operation = st.number_input(
                "Maximum Operation",
                value=None,
                key=f"{prefix}_maximum_operation",
                help="Maximal sum (only operation) of the effect"
            )
            if maximum_operation is not None:
                effect_params["maximum_operation"] = maximum_operation

        # Hourly operation limits
        use_hourly_constraints = st.checkbox(
            "Use Hourly Constraints",
            value=False,
            key=f"{prefix}_use_hourly_constraints"
        )
        if use_hourly_constraints:
            st.write("##### Hourly Operation Limits")
            col1, col2 = st.columns(2)
            with col1:
                min_op_per_hour = smart_numeric_input(
                    "Minimum Operation per Hour",
                    key=f"{prefix}_min_op_per_hour",
                    default_value=0,
                    description="Minimum value per hour (only operation) for each timestep",
                    timesteps=st.session_state.timesteps
                )
                effect_params["minimum_operation_per_hour"] = min_op_per_hour

            with col2:
                max_op_per_hour = smart_numeric_input(
                    "Maximum Operation per Hour",
                    key=f"{prefix}_max_op_per_hour",
                    default_value=100000,
                    description="Maximum value per hour (only operation) for each timestep",
                    timesteps=st.session_state.timesteps
                )
                effect_params["maximum_operation_per_hour"] = max_op_per_hour

    # LAYER 3: Investment Limits
    with st.expander("Investment Limits", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            minimum_invest = st.number_input(
                "Minimum Investment",
                value=0.0,
                key=f"{prefix}_minimum_invest",
                help="Minimal sum (only invest) of the effect"
            )
            if minimum_invest > 0:
                effect_params["minimum_invest"] = minimum_invest

        with col2:
            maximum_invest = st.number_input(
                "Maximum Investment",
                value=0.0,
                key=f"{prefix}_maximum_invest",
                help="Maximal sum (only invest) of the effect"
            )
            if maximum_invest > 0:
                effect_params["maximum_invest"] = maximum_invest

    # LAYER 4: Total Limits
    with st.expander("Total Limits (Operation + Investment)", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            minimum_total = st.number_input(
                "Minimum Total",
                value=0.0,
                key=f"{prefix}_minimum_total",
                help="Minimal sum of effect (invest + operation)"
            )
            if minimum_total > 0:
                effect_params["minimum_total"] = minimum_total

        with col2:
            maximum_total = st.number_input(
                "Maximum Total",
                value=0.0,
                key=f"{prefix}_maximum_total",
                help="Maximal sum of effect (invest + operation)"
            )
            if maximum_total > 0:
                effect_params["maximum_total"] = maximum_total

    # LAYER 5: Specific Share to Other Effects
    with st.expander("Specific Share to Other Effects", expanded=False):
        # Operation shares
        st.write("##### Operation Shares")
        st.write("Define how this effect relates to other effects during operation (e.g., 180 €/t_CO2)")

        # Initialize if not in session state
        operation_shares_key = f"{prefix}_specific_share_operation"
        if operation_shares_key not in st.session_state:
            st.session_state[operation_shares_key] = {}

        operation_shares = dict_editor(
            "Operation Shares",
            key=f"{prefix}_op_shares",
            available_effects=[effect for effect in st.session_state.elements['effects'] if effect != effect_name],
            timesteps=st.session_state.get("timesteps")
        )

        if operation_shares:
            effect_params["specific_share_to_other_effects_operation"] = operation_shares

        # Investment shares
        st.write("##### Investment Shares")
        st.write("Define how this effect relates to other effects for investments")

        # Initialize if not in session state
        invest_shares_key = f"{prefix}_specific_share_invest"
        if invest_shares_key not in st.session_state:
            st.session_state[invest_shares_key] = {}

        invest_shares = dict_editor(
            "Investment Shares",
            key=f"{prefix}_inv_shares",
            available_effects=[effect for effect in st.session_state.elements['effects'] if effect != effect_name],
            timesteps=st.session_state.get("timesteps")
        )

        if invest_shares:
            effect_params["specific_share_to_other_effects_invest"] = invest_shares

    # Create button
    if st.button("Create Effect", key="create_effect"):
        # Create the Effect object
        effect = fx.Effect(**effect_params)

        # Add to system (assuming add_element function exists)
        success, message = add_element(effect, 'effects')

        if success:
            # Display success message
            st.success(message)

            # Display representation of the created object
            with st.expander("Created Effect Details", expanded=True):
                st.write("##### Effect")
                st.json(effect.to_json())
        else:
            st.error(message)

    st.write("---")
    display_existing_effects()


# Display existing effects
def display_effects():
    """Display existing effects in a table"""
    if "flow_system" in st.session_state and st.session_state.flow_system is not None:
        effects = list(st.session_state.flow_system.effects)
        if effects:
            st.subheader("Existing Effects")

            # Create a list of effect data
            effect_data = []
            for effect_name in effects:
                effect = st.session_state.flow_system.get_effect(effect_name)
                if effect:
                    effect_data.append({
                        "Name": effect.label,
                        "Unit": effect.unit,
                        "Description": effect.description,
                        "Is Standard": "✓" if effect.is_standard else "✗",
                        "Is Objective": "✓" if effect.is_objective else "✗"
                    })

            # Display as a dataframe
            if effect_data:
                df = pd.DataFrame(effect_data)
                st.dataframe(df, use_container_width=True)

                # Delete functionality
                col1, col2 = st.columns([3, 1])
                with col1:
                    effect_to_delete = st.selectbox(
                        "Select Effect",
                        options=effects,
                        key="effect_to_delete"
                    )

                with col2:
                    st.write("")  # Spacing
                    if st.button("Delete", key="delete_effect") and effect_to_delete:
                        # Delete the effect (assuming delete_element exists)
                        success = delete_element(effect_to_delete, 'effects')
                        if success:
                            st.success(f"Deleted effect: {effect_to_delete}")
                            st.rerun()
        else:
            st.info("No effects created yet.")
    else:
        st.warning("Flow system not initialized. Create a flow system first.")

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
