import json
import pdb

from core.prompt import *
from core.players.tools.retriever import Retriever
from langchain_openai import ChatOpenAI
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


class Recommender_async:
    def __init__(self, tool, model_name, temperature):
        self.model = ChatOpenAI(model=model_name, temperature=temperature)
        self.tool = tool
        self.reconstructed_profile = Profile()
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
        action = response['Action']
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
            try:
                if self.candidates == []:
                    candidates = self.tool.retriever.select_candidate(self.reconstructed_profile.item_id, self.reconstructed_profile.price_range, self.reconstructed_profile.category_path,
                                                                      self.tool.category_tree)
                    self.candidates.append(candidates[0])
                messages = [
                    SystemMessage(content=chat_system_persuasion.format(conversation_history=conversation_history,
                                                                        thought=self.thoughts[-1]['Thoughts'],
                                                                        item_request=self.reconstructed_profile.preference,
                                                                        user_personality=self.reconstructed_profile.personality,
                                                                        item1=self.selected[0].description,
                                                                        item2=self.candidates[0].description))
                ]

            except:
                # print('No candidate exists')
                messages = [
                    SystemMessage(content=chat_system_persuasion.format(conversation_history=conversation_history,
                                                                        thought=self.thoughts[-1]['Thoughts'],
                                                                        item_request=self.reconstructed_profile.preference,
                                                                        user_personality=self.reconstructed_profile.personality,
                                                                        item1=self.selected[0].description,
                                                                        item2=None))
                ]
            output = await self.model.agenerate([messages], response_format={"type": "json_object"})
            response = output.generations[0][0].text
            # response = response.replace("{{", "{").replace("}}", "}")
            # print(response, "\n")
            response = json.loads(response)
            self.persuasion_strategies.append(response['strategy'])
            return response['sentence']
