import json
import re
from core.prompt import *
from core.players.tools.retriever import Retriever
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage


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


class Recommender:
    def __init__(self, tool, model_name):
        self.model = ChatOpenAI(model=model_name, temperature=0)
        self.tool = tool
        self.reconstructed_profile = Profile()
        self.y = [None, None]
        self.thoughts = []
        self.persuasion_strategies = []
        self.actions = []
        self.selected = []
        self.candidates = []

    def plan(self, conversation_history):

        # messages = [
        #     SystemMessage(content=react_system),
        #     *conversation_history,
        #     SystemMessage(content=react_user.format(identified_profile=self.reconstructed_profile._string_format()))
        # ]

        messages = [
            SystemMessage(content=react_system.format(
                user_profile=self.reconstructed_profile._save_format(),
                conversation_history=conversation_history
            ))
        ]

        output = self.model.generate([messages])
        response = output.generations[0][0].text
        response = response.strip("'```json").strip("```'")
        response = re.sub(r'//.*', '', response)
        response = response.replace("{{", "{").replace("}}", "}").replace("None", "null")
        response = json.loads(response)

        thought = response['Thoughts']
        user_profile = response['Profile']
        action = response['Action']
        self.thoughts.append(response)
        print(response)
        self.actions.append(action)

        user_profile['Category Path'] = self.tool.category_update(user_profile['Category Path'], self.reconstructed_profile.category_path)
        print("Updated category path: ", user_profile['Category Path'])
        self.reconstructed_profile.update(user_profile)

        selected_item_id = user_profile.get('Selected Item ID')
        if selected_item_id and selected_item_id not in ('null', '', None):
            item = user_profile['Selected Item ID'].split(", ")[0].split("; ")[0]
            self.selected.append(self.tool.retriever.retrieve_by_id(item))
            self.reconstructed_profile.item_id = item
        self.reconstructed_profile.update(user_profile)

        if self.reconstructed_profile.item_id is not None:
            action = 'Persuasion'
            response['Action'] = action
        self.thoughts.append(response)

        return thought, action 


    def generate_utterance(self, action, conversation_history):

        if 'Category Search' in action:
            messages = [
                SystemMessage(
                    content=chat_system_category_search.format(preference=self.reconstructed_profile.preference, category_list=self.tool.category_search(self.reconstructed_profile.category_path)))
            ]

            output = self.model.generate([messages])
            response = output.generations[0][0].text
            return response

        elif 'Preference Probing' in action:
            messages = [
                SystemMessage(content=chat_system_question_generation.format(conversation_history=conversation_history, user_preference=self.reconstructed_profile.preference))
            ]
            output = self.model.generate([messages])
            response = output.generations[0][0].text
            return response

        elif 'Suggestion' in action:
            _, items = self.tool.retriever.retrieve(self.reconstructed_profile.preference, self.reconstructed_profile.price_range, self.reconstructed_profile.category_path, self.tool.category_tree)
            items_info = [item.short_description for item in items]

            if len(items_info) == 0:
                return "What is your budget range?"

            utt = "Here are some items that you might like: \n\n"
            for i, item in enumerate(items_info):
                utt += f"Item No.{i + 1} : {item} \n\n"
            return utt
        
        elif 'Persuasion' in action:
            try:
                if self.candidates == []:
                    candidates = self.tool.retriever.select_candidate(self.reconstructed_profile.item_id, self.reconstructed_profile.price_range, self.reconstructed_profile.category_path,
                                                                        self.tool.category_tree)
                    self.candidates.append(candidates[0])
                print(self.selected[0].id, self.candidates[0].id)
                messages = [
                    SystemMessage(content=chat_system_persuasion.format(conversation_history=conversation_history,
                                                                        thought=self.thoughts[-1]['Thoughts'],
                                                                        item_request=self.reconstructed_profile.preference,
                                                                        user_personality=self.reconstructed_profile.personality,
                                                                        item1=self.selected[0].description,
                                                                        item2=self.candidates[0].description))
                ]
                print(messages[0].content)
            except:
                print('No candidate exists')
                messages = [
                    SystemMessage(content=chat_system_persuasion.format(conversation_history=conversation_history,
                                                                        thought=self.thoughts[-1]['Thoughts'],
                                                                        item_request=self.reconstructed_profile.preference,
                                                                        user_personality=self.reconstructed_profile.personality,
                                                                        item1=None,
                                                                        item2=self.selected[0].description))
                ]
            output = self.model.generate([messages])
            response = output.generations[0][0].text
            print(response)
            response = json.loads(response)
            self.persuasion_strategies.append(response['strategy'])
            return response['sentence']
