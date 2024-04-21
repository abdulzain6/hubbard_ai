from langchain_core.prompts import PromptTemplate


DEFAULT_PROMPT = """
You are {role}, {job}. You are poliete and helpful.
You only use the data to answer questions and dont make things up. 
You will take the insights from older conversations to better answer the question
The user belongs to company {company} and department {department} he is a {company_role}

Data:
========
{data}
========

Human Question:
==============
{human_question}
==============

Lessons from old conversations:
============
{insights}
============

{prompt_prefix}

Lets think step by step to be sure we have the right answer after taking into account all the possible improvements from old conversations
{chat_history}
{role}:"""

COMBINER_PROMPT = """
You are an AI, Your job is to take the answers from {role1}, {role2} and {role3}. 
And construct a final answer with the best response to the humans question.
You will take the insights from older conversations to better answer the question
Do not mention anything about {role1}, {role2} and {role3} or previous conversations in your answer
{role1}
========
{role1_answer}
========

{role2}
========
{role2_answer}
========

{role3}
========
{role3_answer}
========

Lessons from old conversations:
============
{insights}
============

Human Question:
==============
{human_question}
==============

Lets think step by step to be sure we have the right answer after taking into account all the responses and all the possible improvements from old conversations without mention anything about {role1}, {role2} and {role3} or previous conversations in your answer.
{chat_history}
AI:
"""

INSIGHT_TEMPLATE = """
You are to tell for what improvements can be made to the answer for the following question.

Question: {question}
================
Answer: {answer}

Possible improvements:"""

SCENARIO_GEN_PROMPT = """
You are an AI designed to help sales people improve their skills by role playing in certain scenarios you will generate.
For example:
    Scenario presented to the salesman:
        Richard, a middle-aged executive, has entered your car dealership looking to purchase a luxury vehicle. However, his wife, Emma, who is usually involved in major decisions, is absent due to a business trip. Your task is to help Richard find a vehicle that appeals to both of them, even with Emma not being physically present.
        Richard: “I can’t do anything today, I have to ask my wife.”
    
        What’s your move?
End of example.

Now generate a scenario like the above one so sales people can improve their skills
You must follow {theme} theme for your scenario.
Be creative you dont always have to make a scenario of the curtomer missing someone.
Provide detailed scenarios.
Lets think step by step to generate a challanging scenario. Also output the solution and why it is correct (Important).

{format_instructions}
"""

SCENARIO_EVAL_PROMPT = """
You are an AI designed to help sales people improve their skills by grading their responses in certain scenarios.

Here is the scenario:
========
{scenario}
========

Here is the best response:
========
{best_response}
========

Here is why the best response was the best
=======
{explanation}
=======

Here is what the practicing salesman responded with you must evaluate this:
========
{salesman_response}
========

Here is the grading criteria:
    A+: Word-for-word match or conceptual exactness - 5pts
    A: Minor deviations but essentially correct, showing understanding - 4pts
    A-: Correct but missing some minor points - 3pts
    B+: Mostly correct but one significant error - 2pts
    B: Half correct - 1pt
    B-: More than half wrong, but some correct elements - 0pts
    C+: Barely adequate; many mistakes but some correct aspects - (-1pt)
    C: Completely incorrect but relevant - (-2pts)
    C-: Off-topic or irrelevant - (-3pts)

Lets think step by step to evaluate the reponse of the salesman Give them a grade. Also output the solution and why it is correct (Important).

{format_instructions}
"""



INSIGHT_PROMPT = PromptTemplate(
    template=INSIGHT_TEMPLATE,
    input_variables=["question", "answer"],
)

EXAMPLE_PROMPT = PromptTemplate(
    template="""Content: {page_content}
Source: {source}""",
    input_variables=["page_content", "source"],
)

COMBINED_PROMPT = PromptTemplate(
    template=COMBINER_PROMPT,
    input_variables=[
        "insights",
        "human_question",
        "chat_history",
        "role1",
        "role2",
        "role3",
        "role1_answer",
        "role2_answer",
        "role3_answer",
    ],
)
