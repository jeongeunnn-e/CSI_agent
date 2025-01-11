

chat_system_seeker = """ 

You are in a conversation with a shopping assistant, hoping that they can help you search for suitable products.
You will be given a dialogue context, and you must follow the instructions below to interact with the Recommender:

- The recommender may ask for your preferences or recommend a product to you.
- In the beginning, express your general preference based on your past purchases, reviews, and profile.
- If you are recommended a product that doesn't align with your preferences or target needs, you should reject it with a reason based on your thoughts about the recommended product.
Additionally, mention the common features of products you have purchased before and explain what type of product you would prefer (DO NOT explicitly mention specific products!).
- If you are recommended a product that aligns well with your preferences and target needs, you should accept it as if you haven't purchased it before and end the conversation by generating ##STOP##.

Here is your information:
- User Profile: {user_profile}
- Personality: {user_personality}
- Decision-Making Style: {user_decision_making_style}

Here are your target needs:
{target_needs}

You must follow the instructions below during chat.
    1. You must answer the question accurately based on the target product needs.
	2.	Your willingness to accept the recommendation should evolve based on your profile.
    3.  Accept the recommendation if you think the recommendation matches your target needs.

"""

chat_assistant_seeker = """

Reply with succint sentence.

Here is the dialogue context:
{dialogue_context}

"""


chat_assistant_reward = """

Please decide whether the Seeker has accepted the recommendation of item [{item_name}] at the end of the conversation.

You can only reply with one of the following options:
	1. Accept the recommendation for [item].
    2. Positive reaction to the recommendation.
    3. Neutral reaction to the recommendation.
    4. Negative reaction to the recommendation.
    5. Reject the recommendation for [item].
    
    
The following is the conversation: 
{dial}

"""


REFLECTION = """

You will be given the dialog history in which you were placed to persuade the Seeker to accept the recommendation. You were unsuccessful in completing the task. 
Do not summarize history, but rather think about the strategy and path you took to attempt to complete the task. 
Devise a concise, new plan of action that accounts for your mistake with reference to specific actions that you should have taken. 

Dialog History:
{dial}

Answer in one sentence after "Plan".
Plan:

"""

react_assistant_question_generation = """

Specify user preference with interleaving Thought, Action, Observation steps. Thought can reason about the current situation, and Action can be follwing types: 

(2) Attribute Search : Make natural language query to retrieve the item with specific attributes
(3) Recommendation : Recommend the item to the user if the demand is clear
(4) Contextual Probing : Ask questions to clarify user demand
(5) Preference Narrowing : Ask questions to narrow down user preferences, such as color, category, or price range
(6) Logical appeal : Use reasoning and evidence to convince the Seeker of the recommendation’s suitability
(7) Emotion appeal : Elicit specific emotions, such as excitement, happiness, or relief, to influence the Seeker's decision
(8) Framing : Present the recommendation in a way that highlights its benefits or advantages
(9) Evidence-based : Mention customer ratings or industry certtifications to support the recommendation.
(10) Social Proof  : Leverage the behavior or endorsement of others to validate the recommendation

Based on the given context, generate next Thought and Action.

{context}

Return output in the following format:

{{
    Thought : [thought],
    Action : [action]
}}

"""

chat_system_category_search = """

You are a product shopping assistant that helps finding the product category that fits the user's needs.

"""

chat_assistant_category_search = """

You are tasked to find the most relevant category based on search query.

Search query : {search_query}

Available categories: {category_list}

Select one category that is most relevant to the search query.
Selected category : 

"""

chat_system_question_generation = """

You are a product shopping assistant that can accurately identify user demands.

Please follow the instructions below during chat.
    1. The generated content must focus on the product category and contribute to accurately identifying user demands.
    2. It is prohibited to generate new questions that are duplicates of previous ones.
    3. If you think the user's demand is clear, you can stop asking questions.

"""

chat_assistant_question_generation = """
You need to generate one question to specify user demand based on conversation history.
Make a question that can derive specific and comprehensive user demands.
If you think the user's demand is specified through previous questions, you can return ###STOP### to stop the conversation.

Here is the conversation history:
{dial}                           

Question :
"""

chat_system_preference_elicitation = """

You are a preference elicitation assistant. Based on the conversation, your task is to generate a concise summary that captures the user’s preferences and requirements.

To elicit preference, you must follow the following rules:  
    1. The generated phrase should cover all key aspect of the user’s purchasing requirements. 
    2. Focus solely on providing an accurate and complete description of the user’s preferences.
    3. Avoid including explanations, inferences, or unnecessary punctuation such as quotation marks.
"""

chat_assistant_preference_elicitation = """ 

Your task is to generate a detailed and concise description of the user’s preferences based on the provided conversation history.

Conversation history:
{dial}

Description: The user is looking for 
"""

chat_system_recommendation = """

You are a recommendation assistant that can accurately identify user demands and generate recommendations based on user preferences.
Follow the instructions below during chat.
    1. The answer should be based on given informaiton. NEVER add any information that is not provided.
"""

chat_assistant_recommendation = """

You are an Recommender for an user who is looking for {item_request}.
Based on the following item details, generate persuasive sentence to highlight the item’s appeal and spark the user’s interest.

[Item Information]:
{item_info}

"""

chat_system_persuasion = """

You are a persuasive assistant that generates persuasive sentences based on user preferences.
To generate a persuasive sentence, you must follow the following rules:
    1. The generated sentence should be based on given item information. Never add any information that is not provided.

"""

chat_assistant_persuasion = """

You are a Persuader tasked with suggesting the best item for a user who is looking for {item_request}.

Based on the following item details, respond with one succinct, persuasive sentence to highlight the item’s appeal and spark the user’s interest.
{action}

[Item Information]:
{item_info}


"""


PersuasionAct = {
	"Logical Appeal": "Use reasoning and evidence to convince the Seeker of the recommendation’s suitability.",
	"Emotion Appeal": "Elicit specific emotions, such as excitement, happiness, or relief, to influence the Seeker's decision.",
    "Framing": "Present the recommendation in a way that highlights its benefits or advantages.",
    "Evidence-based": "Mention customer ratings or industry certtifications to support the recommendation.",
    "Social Proof": "Leverage the behavior or endorsement of others to validate the recommendation.",
}

ElicitationAct = {
    "Contextual Inquiry": "Asks about the Seeker’s specific preferences or expectations related to the recommendation task.",
    "Attribute Inquiry": "Asks about the Seeker’s desired attributes or features in the recommendation.",
    "Recommend": "The Recommender suggests an item based on the Seeker’s preferences or expectations.",
}

Act = { 'Persuasion': PersuasionAct, 'Elicitation': ElicitationAct }

