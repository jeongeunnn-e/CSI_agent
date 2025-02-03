import json

from core.prompt import *
from core.retrieve import Retriever
from core.players.tools.tool import *
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage


class Memory:
    def __init__(self):
        self.preference = None
        self.personality = None
        self.category = None
        self.category_path = None

    def update(self, thought):
        self.preference = thought['Preference']
        self.personality = thought['Personality']
        self.budget_range = thought['Budget Range']
        return self
    
    def _save_format(self):
        return {
            'Preference': self.preference,
            'Personality': self.personality,
            'Category': self.category,
            'Category Path': self.category_path
        }
    

class Recommender:
    def __init__(self, retriever):
        self.planner = ChatOpenAI(model='gpt-4o-mini')
        self.model = ChatOpenAI(model='gpt-4o-mini')
        self.retriever = retriever
        self.memory = Memory()


    def plan(self, conversation_history):

        messages = [
            SystemMessage(content=react_system),
            *conversation_history,
            HumanMessage(content=react_user)
        ]

        output = self.planner.generate([messages])
        response = output.generations[0][0].text
        response = response.strip("'```json").strip("```'")
        response = response.replace("{{","{").replace("}}","}")
        print(response, "\n")
        response = json.loads(response)

        thought = response['Thoughts']
        action = response['Action']

        self.memory.update(thought)

        return thought, 'Category Narrowing'
    
    def generate_utterance(self, action, conversation_history):
        
        if action in ['Category Narrowing']:
            utt = singleq_category_narrow.format(paths_options=category_search(self.memory.category_path))
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
            _, items = self.retriever.retrieve(self.memory.preference)
            items_info = [ item.short_description for item in items ]
            
            utt = "Here are some items that you might like: \n"
            for i, item in enumerate(items_info):
                utt += f"{i+1}. {item}\n"

            return utt

        else:
            messages = [
                SystemMessage(content=chat_system_persuasion),
                *conversation_history,
                HumanMessage(content=chat_system_persuasion.format(action=UnifiedAct[action]))
            ]

            output =self.model.generate([messages])
            response = output.generations[0][0].text
            return response


    def update_memory(self, thought):

        self.memory['Preference'] = thought['Preference']
        self.memory['Personality'] = thought['Personality']
        
        return self.memory

    