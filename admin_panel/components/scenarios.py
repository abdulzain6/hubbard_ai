import streamlit as st
from utils import generate_scenario, evaluate_scenario, add_scenario, delete_scenario, get_all_scenarios, update_scenario, get_files, generate_scenario_metadata

def fetch_scenarios(access_token: str):
    """Fetch all scenarios and store them in session state."""
    response, status = get_all_scenarios(access_token)
    if status == 200:
        st.session_state.scenarios = response
    else:
        st.error("Failed to fetch scenarios")
        
def fetch_files(access_token: str):
    """Fetch all files and store them in session state."""
    response = get_files(access_token)
    st.session_state.files_scenarios = [file['file_name'] for file in response]
   
        
def main():
    st.title("Scenario Evaluation App")

    access_token = st.session_state.get('access_token', '')
    fetch_files(access_token=access_token)

    if not access_token:
        st.warning("You are not logged in.")
        return
    
    st.title("Scenario Management System")

    # Tabs for different functionalities
    tab1, tab2 = st.tabs(["Manage Scenarios", "Generate and Evaluate Scenarios"])

    with tab1:
        st.header("Manage Scenarios")
        st.subheader("Add Scenario")
        with st.form(key='add_scenario_form'):
            name = st.text_input("Scenario Name")
            prompt = st.text_area("Scenario Prompt")
            if "files_scenarios" not in st.session_state:
                fetch_files(access_token)
                
            file_names = st.multiselect("File Names", options=st.session_state.files_scenarios)
            add_button = st.form_submit_button("Add Scenario")
            if add_button:
                response, status = add_scenario(name, prompt, file_names, access_token)
                st.write(f"Response: {response}, Status Code: {status}")
                fetch_scenarios(access_token)  # Refresh scenarios

        st.subheader("View All Scenarios")
        if st.button("Get All Scenarios"):
            fetch_scenarios(access_token)

        if "scenarios" in st.session_state:
            scenarios = st.session_state.scenarios
            for scenario in scenarios:
                with st.expander(scenario['name'], expanded=False):
                    st.write(f"**Prompt:** {scenario['prompt']}")
                    st.write(f"**Files:** {', '.join(scenario['file_names'])}")

                    update_prompt = st.text_area("New Scenario Prompt", value=scenario['prompt'], key=f"prompt_{scenario['name']}")
                    valid_default_files = [file for file in scenario['file_names'] if file in st.session_state.files_scenarios]
                    update_file_names = st.multiselect("New File Names", options=st.session_state.files_scenarios, default=valid_default_files, key=f"files_{scenario['name']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Delete", key=f"delete_{scenario['name']}"):
                            delete_response, delete_status = delete_scenario(scenario['name'], access_token)
                            st.write(f"Response: {delete_response}, Status Code: {delete_status}")
                            fetch_scenarios(access_token)  # Refresh scenarios
                    with col2:
                        if st.button("Update", key=f"update_{scenario['name']}"):
                            st.session_state.update_attributes = {"name": scenario['name'], "prompt": update_prompt, "file_names": update_file_names}
                            st.session_state.update_name = scenario['name']
                            st.session_state.update_trigger = True

        if "update_trigger" in st.session_state and st.session_state.update_trigger:
            update_response, update_status = update_scenario(st.session_state.update_name, st.session_state.update_attributes, access_token)
            st.write(f"Response: {update_response}, Status Code: {update_status}")
            st.session_state.update_trigger = False
            fetch_scenarios(access_token)  # Refresh scenarios
        
    with tab2:
        st.header("Generate and Evaluate Scenarios")

        st.subheader("Generate Scenario")
        # Fetch available scenarios to pick from
        scenario_options = []
        response, status = get_all_scenarios(access_token)
        if status == 200:
            scenario_options = [scenario['name'] for scenario in response]
        scenario_name = st.selectbox("Select Scenario for Generation", scenario_options)

        if st.button("Generate Scenario"):
            st.subheader("Scenario:")
            scenario_response = st.write_stream(
                generate_scenario(scenario_name, access_token)
            )
            scenario_metadata_response = generate_scenario_metadata(scenario_response, access_token)
            if scenario_metadata_response.status_code != 200:
                st.error("Error generating scenario")
            else:
                st.session_state.scenario_response = scenario_response
                st.session_state.scenario_metadata_response = scenario_metadata_response.json()

        if 'scenario_metadata_response' in st.session_state:
            generated_scenario = st.session_state.scenario_metadata_response
            st.markdown(f"**Description:** {generated_scenario['description']}")
            st.markdown(f"**Difficulty:** {generated_scenario['difficulty']}")
            st.markdown(f"**Importance:** {generated_scenario['importance']}")

            salesman_response = st.text_area("Salesman Response")

            if st.button("Evaluate Scenario"):
                eval_response, eval_status = evaluate_scenario(
                    generated_scenario.get("name"),
                    generated_scenario.get("description"),
                    st.session_state.scenario_response,
                    generated_scenario.get("best_response"),
                    generated_scenario.get("explanation"),
                    generated_scenario.get("difficulty"),
                    generated_scenario.get("importance"),
                    salesman_response,
                    access_token
                )
                
                if eval_status == 200:
                    st.subheader("Evaluation Result")
                    st.markdown(f"**Grade:** {eval_response['grade']}")
                    st.markdown(f"**Message:** {eval_response['message']}")
                    st.markdown(f"**Best Response:**\n{eval_response['best_response']}")
                else:
                    st.write(f"Error: {eval_response}")
                    
if __name__ == "__main__":
    main()
