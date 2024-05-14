import streamlit as st
from utils import generate_scenario, evaluate_scenario

def main():
    st.title("Scenario Evaluation App")

    access_token = st.session_state.get('access_token', '')

    if not access_token:
        st.warning("You are not logged in.")
        return

    st.header("Generate a Scenario")
    theme = st.text_input("Enter the theme for the scenario")

    if st.button("Generate Scenario"):
        with st.spinner("Generating scenario..."):
            scenario, status_code = generate_scenario(theme, access_token)
            if status_code == 200:
                st.session_state['scenario'] = scenario
                st.success("Scenario generated successfully")
            else:
                st.error("Failed to generate scenario")

    if 'scenario' in st.session_state:
        scenario = st.session_state['scenario']
        st.subheader("Generated Scenario")
        
        with st.expander("Scenario Details"):
            st.markdown(f"**Name:** {scenario['name']}")
            st.markdown(f"**Description:** {scenario['description']}")
            st.markdown(f"**Scenario:**\n{scenario['scenario']}")
            st.markdown(f"**Difficulty:** {scenario['difficulty']}")
            st.markdown(f"**Importance:** {scenario['importance']}")

        st.header("Evaluate the Scenario")
        salesman_response = st.text_area("Enter the salesman's response", height=200)

        if st.button("Evaluate Response"):
            with st.spinner("Evaluating response..."):
                result, status_code = evaluate_scenario(
                    scenario_name=scenario['name'],
                    scenario_description=scenario['description'],
                    scenario_text=scenario['scenario'],
                    best_response=scenario['best_response'],
                    explanation=scenario['explanation'],
                    difficulty=scenario['difficulty'],
                    importance=scenario['importance'],
                    salesman_response=salesman_response,
                    access_token=access_token
                )
                if status_code == 200:
                    st.success("Response evaluated successfully")
                    st.subheader("Evaluation Result")
                    st.markdown(f"**Grade:** {result['grade']}")
                    st.markdown(f"**Message:** {result['message']}")
                    st.markdown(f"**Best Response:**\n{result['best_response']}")
                else:
                    st.error("Failed to evaluate response")

if __name__ == "__main__":
    main()
