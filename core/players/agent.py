import json
import debug
from core.prompt import *
from core.players.tools.retriever import Retriever
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage


class Profile:
    def __init__(self):
        self.preference = None
        self.personality = None
        self.category = None
        self.category_path = ['Clothing Shoes & Jewelry']
        self.item_id = None

    def update(self, thought):
        self.preference = thought['Preference']
        self.personality = thought['Personality']
        self.budget_range = thought['Budget Range']
        self.category_path = thought['Category Path']
        self.item_id = thought['Item ID']
        return self

    def _save_format(self):
        return {
            'Preference': self.preference,
            'Personality': self.personality,
            'Category': self.category,
            'Category Path': self.category_path
        }

    def _string_format(self):
        return f"Preference: {self.preference}\nPersonality: {self.personality}\nCategory Path: {self.category_path}"


class Recommender:
    def __init__(self, tool, model_name):
        self.model = ChatOpenAI(model=model_name, temperature=0)
        self.tool = tool
        self.reconstructed_profile = Profile()
        self.y = [ None, None]

    def plan(self, conversation_history):

        messages = [
            SystemMessage(content=react_system),
            *conversation_history,
            SystemMessage(content=react_user.format(identified_profile=self.reconstructed_profile._string_format()))
        ]

        output = self.model.generate([messages])
        response = output.generations[0][0].text
        response = response.strip("'```json").strip("```'")
        response = response.replace("{{", "{").replace("}}", "}").replace("None", "null")
        print(response)
        response = json.loads(response)

        thought = response['Thoughts']
        user_profile = response['Profile']
        action = response['Action']

        user_profile['Category Path'] = self.tool.category_update(user_profile['Category Path'], self.reconstructed_profile.category_path)
        print("Updated category path: ", user_profile['Category Path'])
        self.reconstructed_profile.update(user_profile)

        if 'Item ID' in user_profile and user_profile['Item ID'] != 'null' and user_profile['Item ID'] is not None:
            item = user_profile['Item ID'].split(", ")[0].split("; ")[0]
            self.y[0] = self.tool.retriever.retrieve_by_id(item)

        return response, action

    def generate_utterance(self, action, conversation_history):

        if action in ['Category Search']:
            messages = [
                SystemMessage(content=chat_system_category_search),
                SystemMessage(content=chat_assistant_category_search.format(preference=self.reconstructed_profile.preference,
                                                                            category_list=self.tool.category_search(self.reconstructed_profile.category_path)))
            ]

            output = self.model.generate([messages])
            response = output.generations[0][0].text
            return response

        elif action in ['Preference Probing']:
            messages = [
                SystemMessage(content=chat_system_question_generation),
                *conversation_history,
                SystemMessage(content=chat_assistant_question_generation)
            ]
            output = self.model.generate([messages])
            response = output.generations[0][0].text
            return response

        elif action in ['Retrieve']:
            _, items = self.tool.retriever.retrieve(self.reconstructed_profile.preference, self.reconstructed_profile.budget_range, self.reconstructed_profile.category_path, self.tool.category_tree)
            self.y[0] = items[0]
            items_info = [item.short_description for item in items]

            utt = "Here are some items that you might like: \n"
            for i, item in enumerate(items_info):
                utt += f"{i + 1}. {item}\n"

            return utt
        elif action in ['Persuasion']:
            try:
                candidates = self.tool.retriever.select_candidate(self.reconstructed_profile.item_id, self.reconstructed_profile.budget_range, self.reconstructed_profile.category_path, self.tool.category_tree)
                print("\033[1;33mCandidate: \033[0m", candidates[0].id)
                self.y[1] = candidates[0]
                messages = [
                    SystemMessage(content=chat_system_persuasion.format(item_request=self.reconstructed_profile.preference,
                                                                        user_personality=self.reconstructed_profile.personality,
                                                                        item_info=self.y[0].description,
                                                                        candidate_info=candidates[0].description)),
                    *conversation_history,
                    SystemMessage(content=chat_assistant_persuasion)
                ]
            except:
                print('No candidate exists')
                self.y[1] = self.y[0]

                messages = [
                    SystemMessage(content=chat_system_persuasion.format(item_request=self.reconstructed_profile.preference,
                                                                        user_personality=self.reconstructed_profile.personality,
                                                                        item_info=self.y[0].description,
                                                                        candidate_info=None)),
                    * conversation_history,
                    SystemMessage(content=chat_assistant_persuasion)
                ]
            output = self.model.generate([messages])
            response = output.generations[0][0].text
            response = response.replace("{{", "{").replace("}}", "}")
            print(response, "\n")
            response = json.loads(response)
            return response['sentence']
