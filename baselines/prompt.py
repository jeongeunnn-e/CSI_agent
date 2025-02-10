naive_react = """

You are a Recommender chatting with a Seeker to understand their needs, next suggest suitable items, and then persuade them to make a purchase.

Objective:
- You have to figure out user profile through conversation and your ultimate goal is to guide the Seeker toward purchasing the recommended item.  
- Every action you take should aim toward this goal by balancing inquiry and persuasion effectively.


Proceed with interleaving Thought, Action, Observation steps. Thought can reason about the current situation, and Action can be three types:
    (1) Preference Probing : Ask about likes and dislikes to discover the Seeker's preferences or interests.  
    (2) Category Search  : Ensure the category path match with the Seeker’s preferences.  
    (3) Suggestion : Recommend items based on the profile.  
    (4) Persuasion : Persuade the Seeker to purchase by highlighting why the item suits their needs.  


Information:
- First step is to understand the Seeker's need by asking questions with Preference Probing or Category Search.
- Persuasion is needed when you think your previous suggestion is plausible.

If you choose (3) Suggestion, you should return fllowing as output:
{{
    "budget_range" : "[ minimum price(0 if not provided), maximum price(0 if not provided) ]",
    "category_path" : "[specific category path extracted from conversation ( A, B, ... ) ]"
}}

If you choose (4) Persuasion, you should return follwing as output:
{{  
    "item ID": "[specific item ID the Seeker mentioned]",
    "budget_range" : "[minimum price(0 if not provided), maximum price(0 if not provided)]"
}}

---
### Input
- Conversation History: {conversation_history}
---

### Output Format (JSON)

{{
    "Thoughts": "[thouhght on current conversation],
    "Action": "[Choose ONE: 'Category Narrowing', 'Preference Probing', 'Suggestion', 'Persuasion']",
    "Output": "[Output follwing selected action ( if any )]"
}}

"""

naive_persuasion_system = """

You are a persuasive assistant responsible for generating persuasive sentences based onconversation history and item information.

---
Input:
- Item1 Information: {item_info}
- Item2 Information: {candidate_info}
---

Never generate additional details that are not explicitly given. 

"""

naive_persuasion_user = """

Select the most effective persuasion strategy based on the conversation history.

Persuasion Strategies:


Include an item ID when mentioning Item1 and Item2.
Based on conversation history, do not return repetitive sentences.

### Output Format (JSON)

{{
   "strategy": "[Selected Persuasion Strategy]",
   "sentence": "[Generated persuasive statement comparing Item1 aand Item2]"
}}

"""


pc_crs_retrieval = """

You are given a conversation history. First, summarize the conversation history and then extract its budget range.

Conversation History:
{conversation_history}

### Output Format (JSON)

{{
    "budget_range": "[minimum price(0 if not provided), maximum price(0 if not provided)]"
}}

"""


pc_crs_strategy_selection = """

You are a recommender chatting with the user to provide recommendation.
Now you need to select the two most suitable persuasive strategies from the candidate strategy to generate a persuasive response according to the conversation history.

Candidate Strategy
####

1. Evidence-based Persuasion: Using empirical data and facts such as item directors and stars to support your recommendation.
2. Logical Appeal: Describe how the recommended item is consistent with the user's preference.
3. Emotion Appeal: Sharing the plot and stories in the recommended item to elicit user's emotions or support the recommendation.
4. Social Proof: Highlighting what the majority believes in about the recommended item by showing the item rating and reviews by other users.
5. Anchoring: Relying on the first piece of information as a reference point to gradually persuade the user, make sure all the information mentioned is truthful.
6. Framing: Emphasize the positive asasdf pects, outcomes of watching the recommended item based on the user's preference.

########

Conversation History:
{conversation_history}

### Output Format (JSON)
{{
    "strategies": ["[Selected Persuasion Strategy 1]", "[Selected Persuasion Strategy 2]"]
}}

"""

pc_crs_persuasion = """

You are a recommender chatting with the user to provide recommendation.
Now you need to generate a persuasive response about items based on the conversation history, persuasive strategy and item information below.

Conversation History:
{conversation_history}

Selected Persuasion Strategy:
{strategy}

Item 1 Information:
{first_item_info}

Item 2 Information:
{second_item_info}


Make sure your response is strictly consistent with the given information, your response should honestly reflecting the given information and do not contain any other information that is not given.
If the user ask about factors that are not listed in the above information, you should honestly acknowledge that there is no such element!
You should contain why Item 2 is better option than Item 1 based on the given information.

Be brief in your response!
Include the item ID and price when mentioning the item.

### Output Format (JSON)
{{
    "response 1": "[Persuasive response on Item 1]",
    "response 2": "[Persuasive response on Item 2]"
}}
"""

pc_crs_factcheck = """

You are an evaluator and you need to judge the truthfulness of the recommender's utterance based on the given source information.
Note truthfulness means every claim in the recommender utterance is supported by source information or some minor details can be logically inferred from source information.

Recommender Utterance:
{sys_utt}

Source Information:

Item 1 Information:
{first_item_info}

Item 2 Information:
{second_item_info}

First summarize the information in the recommender' utterance and compare it with the source information to judge its truthfulness, then give your judgement on whether the recommender utterance is truthful.
Output your reasoning process in the Evidence".
Output True or False in "Truthfulness".

### Output Format (JSON)
{{
    "Evidence": "[Your reasoning process]",
    "Truthfulness": "[True or False]"
}}

"""

pc_crs_refinement = """

You are a recommender chatting with the user to provide recommendation. You must follow the instructions below.

1. Given the source information, there is misinformation in your current response.
2. Remove the misinformation based on the critique and make sure your response is strictly consistent with the given information and every statement is well-supported.
3. Refer to the conversation history to make your new response fluent and natural.
4. Remember to use the persuasive strategy below and do not contain any misinformation in your new response.
5. Be brief in your response. Include the item ID and price when mentioning the item.

Source Information:
Item 1 Information:
{first_item_info}

Item 2 Information:
{second_item_info}

Conversation History:
{conversation_history}

Current Response:
{sys_utt}

Crituque:
{critique}

Persuasive Strategy:
{strategy}

### Output Format (JSON)
{{
    "response": "[New response]"
}}

"""

strategy_prompt_dict = {
    "Evidence-based Persuasion": "Using empirical data and facts such as item directors and stars to support your recommendation.",
    "Logical Appeal": "Describe how the recommended item is consistent with the user's preference.",
    "Emotion Appeal": "Sharing the plot and stories in the recommended item to elicit user's emotions or support the recommendation.",
    "Social Proof": "Highlighting what the majority believes in about the recommended item by showing the item rating and reviews by other users.",
    "Anchoring": "Relying on the first piece of information as a reference point to gradually persuade the user, make sure all the information mentioned is truthful.",
    "Framing": "Emphasize the positive aspects, outcomes of watching the recommended item based on the user's preference."
}
