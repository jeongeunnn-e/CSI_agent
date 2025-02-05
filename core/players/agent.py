import json

from core.prompt import *
from core.players.tools.retriever import Retriever
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage


class Profile:
    def __init__(self):
        self.preference = None
        self.personality = None
        self.category = None
        self.category_path = [ 'Clothing, Shoes & Jewelry']

    def update(self, thought):
        self.preference = thought['Preference']
        self.personality = thought['Personality']
        self.budget_range = thought['Budget Range']
        self.category_path = thought['Category Path']
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
        self.model = ChatOpenAI(model=model_name)
        self.tool = tool
        self.memory = Profile()
        self.accumulated_history = []

    def plan(self, conversation_history):

        messages = [
            SystemMessage(content=react_system),
            *conversation_history,
            HumanMessage(content=react_user.format(identified_profile=self.memory._string_format()))
        ]

        output = self.model.generate([messages])
        response = output.generations[0][0].text
        response = response.strip("'```json").strip("```'")
        response = response.replace("{{","{").replace("}}","}").replace("None", "null")
        response = json.loads(response)
        print(response)
        
        thought = response['Thoughts']
        user_profile = response['User Profile']
        action = response['Action']

        user_profile['Category Path'] = self.tool.category_update(user_profile['Category Path'], self.memory.category_path)
        print("Updated category path: ", user_profile['Category Path'])
        self.memory.update(user_profile)

        if 'Item ID' in user_profile and user_profile['Item ID'] is not None and user_profile['Item ID'] != 'null':
            if isinstance(user_profile['Item ID'], list):
                item = user_profile['Item ID'][0]
                if item is not None:
                    self.recommendation = self.tool.retriever.retrieve_by_id(item)
            else:
                item = user_profile['Item ID'].split(", ")[0].split("; ")[0]
                self.recommendation = self.tool.retriever.retrieve_by_id(item)

        return thought, action
    

    def generate_utterance(self, action, conversation_history):
        
        if action in ['Category Narrowing']:
            messages = [
                SystemMessage(content=chat_system_category_search),
                HumanMessage(content=chat_assistant_category_search.format(search_query=self.memory.preference,
                                                                            category_list=self.tool.category_search(self.memory.category_path)))
            ]
            
            output =self.model.generate([messages])
            response = output.generations[0][0].text
            for prefix in ["Selected category : ", "Selected category: "]:
                if prefix in response:
                    response = response.split(prefix)[1]
                break

            utt = f"Are you looking for following category : {response}?"
            return utt
        
        elif action in ['Preference Probing']:
            messages = [
                SystemMessage(content=chat_system_question_generation),
                *conversation_history,
                HumanMessage(content=chat_assistant_question_generation)
            ]
            output =self.model.generate([messages])
            response = output.generations[0][0].text
            return response
        
        elif action in ['Retrieve']:
            _, items = self.tool.retriever.retrieve(self.memory.preference, self.memory.category_path, self.tool.category_tree)
            self.recommendation = items[0]
            items_info = [ item.short_description for item in items ]
            
            utt = "Here are some items that you might like: \n"
            for i, item in enumerate(items_info):
                utt += f"{i+1}. {item}\n"

            return utt
        elif action in ['Persuasion']:
            messages = [
                SystemMessage(content=chat_system_persuasion),
                *conversation_history,
                HumanMessage(content=chat_assistant_persuasion.format(item_request = self.memory.preference,
                                                                      user_personality = self.memory.personality,
                                                                      item_info = self.recommendation.description))  
            ]

            output =self.model.generate([messages])
            response = output.generations[0][0].text
            response = response.replace("{{","{").replace("}}","}")
            print(response, "\n")
            response = json.loads(response)
            return response['sentence']

