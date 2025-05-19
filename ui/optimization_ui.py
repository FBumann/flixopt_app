import streamlit as st
import flixopt as fx
import plotly.graph_objects as go

def render_optimization_tab():
    """Render the Optimization tab UI"""
    st.header("Optimization")

    if st.session_state.flow_system is None:
        st.warning("Please initialize the flow system first in the System Configuration tab.")
        return
    elif not any(st.session_state.elements.values()):
        st.warning("Please add components to your system before running the optimization.")
        return

    # System overview
    st.subheader("System Overview")

    # Count components by type
    component_counts = {
        "Buses": len(st.session_state.elements['buses']),
        "Effects": len(st.session_state.elements['effects']),
        "Converters": len(st.session_state.elements['converters']),
        "Storage Systems": len(st.session_state.elements['storages']),
        "Sources": len(st.session_state.elements['sources']),
        "Sinks": len(st.session_state.elements['sinks'])
    }

    # Create a pie chart for component counts
    fig = go.Figure(data=[go.Pie(
        labels=list(component_counts.keys()),
        values=list(component_counts.values()),
        hole=.3
    )])
    fig.update_layout(title_text="Component Distribution")
    st.plotly_chart(fig, use_container_width=True)

    # Check for objective
    try:
        st.session_state.flow_system.effects.objective_effect
    except KeyError:
        st.warning("⚠️ No objective function defined. Please add at least one effect with 'Is Objective' checked.")

    # Solver settings
    st.subheader("Solver Settings")

    solver_type = st.selectbox(
        "Solver Type",
        ["HiGHS", "GLPK", "CPLEX", "Gurobi"],
        index=0,
        help="Choose which solver to use. Some solvers may require additional installation."
    )

    col1, col2 = st.columns(2)
    with col1:
        gap = st.number_input(
            "Relative Gap",
            min_value=0.001,
            max_value=0.1,
            value=0.01,
            step=0.001,
            format="%.3f",
            help="The optimization will stop when the gap between the best found solution and the best possible solution is less than this value."
        )
    with col2:
        max_time = st.number_input(
            "Maximum Solving Time (seconds)",
            min_value=10,
            max_value=3600,
            value=60,
            step=10,
            help="The maximum time allowed for the solver to find a solution."
        )

    # Advanced solver settings in an expander
    with st.expander("Advanced Solver Settings"):
        col1, col2 = st.columns(2)
        with col1:
            log_level = st.selectbox(
                "Log Level",
                ["Error", "Warning", "Info", "Debug"],
                index=2,
                help="Amount of information to display during solving."
            )

            num_threads = st.number_input(
                "Number of Threads",
                min_value=1,
                max_value=16,
                value=None,
                help="Number of threads to use for parallel solving. Leave empty for automatic selection."
            )

        with col2:
            time_limit_for_preprocessing = st.number_input(
                "Time Limit for Preprocessing (seconds)",
                min_value=1,
                max_value=600,
                value=None,
                help="Maximum time for model preprocessing."
            )

            presolve = st.selectbox(
                "Presolve",
                ["Default", "On", "Off"],
                index=0,
                help="Whether to use the solver's presolve capabilities."
            )

    # Model settings
    st.subheader("Model Settings")

    # Enable or disable specific model features
    col1, col2 = st.columns(2)
    with col1:
        on_off_modeling = st.checkbox(
            "Enable On/Off Modeling",
            value=True,
            help="Enable modeling of component on/off states."
        )

        investment_modeling = st.checkbox(
            "Enable Investment Optimization",
            value=False,
            help="Enable optimization of component sizes."
        )

    with col2:
        use_warm_start = st.checkbox(
            "Use Warm Start",
            value=True,
            help="Use previous solution as starting point if available."
        )

        linear_relaxation = st.checkbox(
            "Use Linear Relaxation",
            value=False,
            help="Solve a linear relaxation of the problem first to speed up solving."
        )

    # Run optimization button
    if st.button("Run Optimization", type="primary", use_container_width=True):
        # Validate system first
        from utils.session_state import validate_system
        valid, validation_issues = validate_system()

        if not valid:
            st.error("Cannot run optimization due to the following issues:")
            for issue in validation_issues:
                st.warning(f"⚠️ {issue}")
            return

        try:
            with st.spinner("Running optimization..."):
                # Create calculation
                calculation = fx.FullCalculation('streamlit model', st.session_state.flow_system)

                # Configure model settings
                model_config = {}
                if not on_off_modeling:
                    model_config['disable_on_off_modeling'] = True

                if not investment_modeling:
                    model_config['disable_investment_optimization'] = True

                # Do modeling with appropriate configuration
                calculation.do_modeling(**model_config)

                # Configure solver based on selection
                if solver_type == "HiGHS":
                    solver = fx.solvers.HighsSolver(gap, max_time)
                elif solver_type == "GLPK":
                    solver = fx.solvers.GLPKSolver(gap, max_time)
                elif solver_type == "CPLEX":
                    solver = fx.solvers.CPLEXSolver(gap, max_time)
                elif solver_type == "Gurobi":
                    solver = fx.solvers.GurobiSolver(gap, max_time)

                # Configure advanced solver settings
                if num_threads is not None:
                    solver.num_threads = num_threads

                if time_limit_for_preprocessing is not None:
                    solver.time_limit_for_preprocessing = time_limit_for_preprocessing

                if presolve != "Default":
                    solver.presolve = (presolve == "On")

                # Set log level
                log_levels = {
                    "Error": 0,
                    "Warning": 1,
                    "Info": 2,
                    "Debug": 3
                }
                solver.log_level = log_levels.get(log_level, 2)

                # Solve the model
                calculation.solve(solver)

                # Store results
                st.session_state.results = calculation.results

                # Calculate some statistics about the solution
                n_variables = calculation.model.n_variables if hasattr(calculation.model, 'n_variables') else "N/A"
                n_constraints = calculation.model.n_constraints if hasattr(calculation.model, 'n_constraints') else "N/A"

                st.success("Optimization completed successfully!")

                # Display objective value(s)
                st.subheader("Optimization Results")

                # Extract objective values
                objective_effects = [effect for effect in st.session_state.elements['effects'] if effect.is_objective]
                if objective_effects:
                    objective_values = {}
                    for effect in objective_effects:
                        try:
                            # Get total effect value
                            value = st.session_state.results.get_total_effect(effect.label)
                            objective_values[effect.label] = value
                        except:
                            objective_values[effect.label] = "N/A"

                    # Display in columns
                    cols = st.columns(len(objective_values))
                    for i, (label, value) in enumerate(objective_values.items()):
                        with cols[i]:
                            st.metric(
                                f"Total {label}",
                                f"{value:.2f}" if isinstance(value, (int, float)) else value
                            )

                # Show model statistics
                st.info(f"""
                    **Model Statistics:**
                    - Variables: {n_variables}
                    - Constraints: {n_constraints}
                    - Solver: {solver_type}
                    - Solution Gap: {gap:.2%}
                """)

                # Suggest to go to Results tab
                st.info("👉 Please go to the Results tab to view detailed results and visualizations.")

        except Exception as e:
            st.error(f"Error during optimization: {str(e)}")