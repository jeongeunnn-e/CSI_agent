import json
import pdb

from core.prompt import *
from core.players.tools.retriever import Retriever
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from collections import Counter


class Profile:
    def __init__(self):
        self.preference = None
        self.personality = None
        self.category_path = ['Clothing Shoes & Jewelry']
        self.item_id = None
        self.price_range = [0, 0]

    def update(self, thought):
        self.preference = thought['Preference']
        self.personality = thought['Personality']
        self.category_path = thought['Category Path']
        self.price_range = thought['Expected Price Range']
        return self

    def _save_format(self):
        return {
            'Preference': self.preference,
            'Personality': self.personality,
            'Category Path': self.category_path,
            "Expected Price Range": self.price_range
        }

    def _string_format(self):
        return f"Preference: {self.preference}\nCategory Path: {self.category_path}\nPersonality: {self.personality}\nExpected Price Range: {self.price_range}\nSelected Item ID: {self.item_id}"


class Recommender_WMemory:
    def __init__(self, tool, memory, args):
        self.model = ChatOpenAI(model=args.rec_model, temperature=args.temperature)
        self.tool = tool
        self.reconstructed_profile = Profile()
        self.memory = memory
        self.mode = args.memory_mode

        self.thoughts = []
        self.actions = []
        self.persuasion_strategies = []
        self.selected = []
        self.candidates = []

    async def plan(self, conversation_history):

        messages = [
            SystemMessage(content=react_system.format(conversation_history=conversation_history, user_profile=self.reconstructed_profile._string_format())),
        ]

        output = await self.model.agenerate([messages], response_format={"type": "json_object"})
        response = output.generations[0][0].text
        # response = response.strip("'```json").strip("```'")
        # response = response.replace("{{", "{").replace("}}", "}").replace("None", "null")
        response = response.replace("None", "null")
        # print(response)
        response = json.loads(response)

        thought = response['Thoughts']
        user_profile = response['Profile']
        action =  response['Action']
        self.actions.append(action)


        user_profile['Category Path'] = self.tool.category_update(user_profile['Category Path'], self.reconstructed_profile.category_path)
        if 'Selected Item ID' in user_profile and user_profile['Selected Item ID'] != 'null' and user_profile['Selected Item ID'] is not None:
            item = user_profile['Selected Item ID'].split(", ")[0].split("; ")[0]
            self.selected.append(self.tool.retriever.retrieve_by_id(item))
            self.reconstructed_profile.item_id = item
        self.reconstructed_profile.update(user_profile)

        if self.reconstructed_profile.item_id is not None:
            action = 'Persuasion'
            response['Action'] = action
        self.thoughts.append(response)

        return thought, action


    async def generate_utterance(self, action, conversation_history):

        if action in ['Category Search']:
            messages = [
                SystemMessage(
                    content=chat_system_category_search.format(preference=self.reconstructed_profile.preference, category_list=self.tool.category_search(self.reconstructed_profile.category_path)))
            ]

            output = await self.model.agenerate([messages])
            response = output.generations[0][0].text

            return response

        elif action in ['Preference Probing']:
            messages = [
                SystemMessage(content=chat_system_question_generation.format(conversation_history=conversation_history, user_preference=self.reconstructed_profile.preference))
            ]
            output = await self.model.agenerate([messages])
            response = output.generations[0][0].text
            return response

        elif action in ['Suggestion']:
            _, items = self.tool.retriever.retrieve(self.reconstructed_profile.preference, self.reconstructed_profile.price_range, self.reconstructed_profile.category_path, self.tool.category_tree)
            items_info = [item.short_description for item in items]

            utt = "Here are some items that you might like: \n"
            for i, item in enumerate(items_info):
                utt += f"Item No.{i + 1} : {item} "
            return utt

        elif action in ['Persuasion']:

            if self.candidates == []:
                candidates = self.tool.retriever.select_candidate(self.reconstructed_profile.item_id, self.reconstructed_profile.price_range, self.reconstructed_profile.category_path,
                                                                    self.tool.category_tree)
                self.candidates.append(candidates[0])

            retrieved = self.get_example_from_memory() if self.mode=='conversation' else self.get_strategy_from_memory()
            if retrieved:
                # print("Using Memory")
                # print(persuasion_strategy)
                if self.mode=='persuasion':
                    persuasion_strategy_prompt, selected_strategy = self.persuasion_with_memory_prompt(retrieved)
                    messages = [
                    SystemMessage(content=persuasion_strategy_prompt.format(conversation_history=conversation_history,
                                                                        selected_strategy=retrieved + ": " + selected_strategy,
                                                                        thought=self.thoughts[-1]['Thoughts'],
                                                                        item_request=self.reconstructed_profile.preference,
                                                                        user_personality=self.reconstructed_profile.personality,
                                                                        item1=self.selected[0].description,
                                                                        item2=self.candidates[0].description))
                    ]
                messages = [
                    SystemMessage(content=chat_system_persuasion.format(conversation_history=conversation_history,
                                                                        example=retrieved,
                                                                        thought=self.thoughts[-1]['Thoughts'],
                                                                        item_request=self.reconstructed_profile.preference,
                                                                        user_personality=self.reconstructed_profile.personality,
                                                                        item1=self.selected[0].description,
                                                                        item2=self.candidates[0].description))
                ]
            else:
                messages = [
                    SystemMessage(content=chat_system_persuasion.format(conversation_history=conversation_history,
                                                                        thought=self.thoughts[-1]['Thoughts'],
                                                                        example="",
                                                                        item_request=self.reconstructed_profile.preference,
                                                                        user_personality=self.reconstructed_profile.personality,
                                                                        item1=self.selected[0].description,
                                                                        item2=self.candidates[0].description))
                ]

            output = await self.model.agenerate([messages], response_format={"type": "json_object"})
            response = output.generations[0][0].text
            # response = response.replace("{{", "{").replace("}}", "}")
            # print(response, "\n")
            response = json.loads(response)
            self.persuasion_strategies.append(response['strategy'])
            return response['sentence']


    def load_reconstructed_profile(self, user_profile):
        user_profile['Category Path'] = self.tool.category_update(user_profile['Category Path'], self.reconstructed_profile.category_path)
        if 'Selected Item ID' in user_profile and user_profile['Selected Item ID'] != 'null' and user_profile['Selected Item ID'] is not None:
            item = user_profile['Selected Item ID'].split(", ")[0].split("; ")[0]
            self.selected.append(self.tool.retriever.retrieve_by_id(item))
            self.reconstructed_profile.item_id = item
        self.reconstructed_profile.update(user_profile)


    def get_strategy_from_memory(self):
        retrieved = self.memory.retrieve_memory(self.reconstructed_profile._string_format(), top_k=3)
        if not retrieved:
            return None
        possible_actions = [action for _, history in retrieved for action in history[0].split("; ")]

        counter = Counter(possible_actions)
        most_common_element = counter.most_common(1)[0][0]
        return most_common_element

    
    def get_example_from_memory(self):
        retrieved = self.memory.retrieve_memory(self.reconstructed_profile._string_format())
        if not retrieved:
            return None
        
        similar_user_profile, memory = retrieved[0]
        memory = memory[0]
        example = "This is an example of your previous statement with a similar user. You can use this as a reference to generate your response.\n"
        example += "user profile:\n" + similar_user_profile + "\n"
        example += "selected strategy:\n" + memory['strategy'] + "\n"
        example += "persuasive statement:\n" + memory['utterance'] + "\n"

        return example


    def persuasion_with_memory_prompt(self, strategy):
        persuasion_with_memory = """

        You are a recommender chatting with the user to provide recommendation.
        Now you need to generate a persuasive response about items based on the input information below.

        ### Objective:
            Use "Persuasion Strategy" to persuasively explain to seeker to purchase item.
            Persuade user to purchase <Candidate Item>.
        ---    
        ### Input information:
        current state analysis: {thought} 
        User Needs: {item_request}
        User Personality: {user_personality}
        <Selected Item> : {item1}
        <Candidate Item> : {item2}
        ---

        Use following persuasion strategy and generate explanations to encourage seeker to purchase.
        ### Persuasion Strategy:
        {selected_strategy}

        ### Output Format (JSON)
        {{
        "sentence": "...."
        }}

        You must include the exact "Item ID" and price when mentioning the item. Follow this format: <"Item Title"> ("Item ID")
        Here is your Conversation History:{conversation_history}
        Generate next utterance. You should choose one item.

        """

        strategy_prompt_dict = {
            "Framing": "Emphasize the unique advantages of <Candidate Item> that differentiate it from <Selected Item>.",
            "Logical Appeal": "Describe how the recommended item's features are consistent with the user’s preference.",
            "Emotional Appeal": "Leverage emotions like anticipation, security, and satisfaction to encourage the purchase.",
            "Evidence-Based Approach": "Using empirical data and facts such as item attributes to support your recommendation.",
            "Social Proof": "Highlighting what the majority believes in about the recommended item by showing the item rating and reviews by other users."
        }

        return persuasion_with_memory, strategy_prompt_dict[strategy]


