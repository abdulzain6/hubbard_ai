import streamlit as st
from utils import evaluate_scenario, get_all_scenarios, create_scenario, update_scenario, delete_scenario, generate_scenario

def main():
    st.title("Scenario Management")
    access_token = st.session_state.get('access_token', '')

    if not access_token:
        st.warning("You are not logged in.")
        return

    tab1, tab2, tab3 = st.tabs(["List & Manage Scenarios", "Create Scenario", "Test Scenarios"])

    # Tab 1: List and Manage Scenarios
    with tab1:
        st.subheader("Existing Scenarios")
        scenarios, status_code = get_all_scenarios(access_token)
        if status_code == 200 and scenarios:
            for scenario in scenarios:
                with st.expander(f"{scenario['name']} - Difficulty: {scenario['difficulty']}"):
                    st.text(scenario['description'])
                    update_form = st.form(key=f"form_update_{scenario['name']}")
                    new_name = update_form.text_input("Name", value=scenario['name'])
                    new_description = update_form.text_area("Description", value=scenario['description'])
                    new_scenario_description = update_form.text_area("Scenario Description", value=scenario['scenario_description'])
                    new_best_response = update_form.text_area("Best Response", value=scenario['best_response'])
                    new_response_explanation = update_form.text_area("Response Explanation", value=scenario['response_explanation'])
                    new_difficulty = update_form.selectbox("Difficulty", options=["A", "B", "C"], index=["A", "B", "C"].index(scenario['difficulty']))
                    new_importance = update_form.selectbox("Importance", options=[1, 2, 3], index=[1, 2, 3].index(scenario['importance']))
                    update_button = update_form.form_submit_button("Update")

                    if update_button:
                        update_data = {
                            "name": new_name,
                            "description": new_description,
                            "scenario_description": new_scenario_description,
                            "best_response": new_best_response,
                            "response_explanation": new_response_explanation,
                            "difficulty": new_difficulty,
                            "importance": new_importance
                        }
                        result, update_status = update_scenario(scenario['name'], update_data, access_token)
                        if update_status == 200:
                            st.success("Scenario updated successfully.")
                            st.rerun()
                        else:
                            st.error(f"Failed to update scenario: {result.get('message', 'Update failed')}")

                    if st.button(f"Delete {scenario['name']}"):
                        result, delete_status = delete_scenario(scenario['name'], access_token)
                        if delete_status == 200:
                            st.success("Scenario deleted successfully.")
                            st.rerun()
                        else:
                            st.error(f"Failed to delete scenario: {result.get('message', 'Delete failed')}")

        else:
            st.error("Failed to retrieve scenarios or no scenarios available.")

    # Tab 2: Create Scenario
    with tab2:
        st.subheader("Create New Scenario")
        with st.form("create_scenario"):
            name = st.text_input("Name")
            description = st.text_area("Description")
            scenario_description = st.text_area("Scenario Description")
            best_response = st.text_area("Best Response")
            response_explanation = st.text_area("Response Explanation")
            difficulty = st.selectbox("Difficulty", options=["A", "B", "C"])
            importance = st.selectbox("Importance", options=[1, 2, 3])
            create_button = st.form_submit_button("Create Manually")

            if create_button:
                data = {
                    "name": name,
                    "description": description,
                    "scenario_description": scenario_description,
                    "best_response": best_response,
                    "response_explanation": response_explanation,
                    "difficulty": difficulty,
                    "importance": importance
                }
                result, create_status = create_scenario(data, access_token)
                if create_status == 200:
                    st.success("Scenario created successfully.")
                else:
                    st.error(f"Failed to create scenario: {result.get('message', 'Create failed')}")

        theme = st.text_input("Theme for Auto-generation")
        if st.button("Generate Scenario Based on Theme"):
            result, generate_status = generate_scenario(theme, access_token)
            if generate_status == 200:
                st.success("Scenario generated successfully:")
                st.json(result)
            else:
                st.error(f"Failed to generate scenario: {result.get('message', 'Generate failed')}")
    
    with tab3:
        st.subheader("Run a Scenario")
        scenario_list, status_code = get_all_scenarios(access_token)
        if status_code == 200 and scenario_list:
            scenario_names = [scenario['name'] for scenario in scenario_list]
            selected_scenario = st.selectbox("Choose a scenario to run", scenario_names)
            selected_scenario_details = next((item for item in scenario_list if item['name'] == selected_scenario), None)
            if selected_scenario_details:
                st.write("Scenario Description:")
                st.info(selected_scenario_details['scenario_description'])
                user_response = st.text_area("Your Response")
                if st.button("Evaluate Response"):
                    result, eval_status = evaluate_scenario(selected_scenario, user_response, access_token)
                    if eval_status == 200:
                        st.success("Response evaluated successfully:")
                        st.json(result)
                    else:
                        st.error(f"Failed to evaluate response: {result.get('message', 'Evaluate failed')}")
        else:
            st.error("Failed to retrieve scenarios or no scenarios available.")


if __name__ == "__main__":
    main()
