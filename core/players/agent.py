import json

from core.prompt import *
from core.retrieve import Retriever

from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage


class Recommender:
    def __init__(self):
        self.planner = ChatOpenAI(model='gpt-4o-mini')
        self.model = ChatOpenAI(model='gpt-4o-mini')
        self.retriever = Retriever()

    def plan(self, conversation_history):

        messages = [
            SystemMessage(content=react_system),
            *conversation_history,
            HumanMessage(content=react_user)
        ]

        output = self.planner.generate([messages])
        response = output.generations[0][0].text
        print(response)
        response = response.strip("'```json").strip("```'")
        response = json.loads(response)

        thought = response['Thoughts']
        action = response['Action'][0]
        self.preference = thought['Preference']

        return thought, action
    
    def generate_utterance(self, action, conversation_history):

        if action in ['Category Narrowing', 'Preference Probing']:
            messages = [
                SystemMessage(content=chat_system_question_generation),
                *conversation_history,
                HumanMessage(content=chat_assistant_question_generation)
            ]
            output =self.model.generate([messages])
            response = output.generations[0][0].text
            return response
        
        elif action in ['Retrieve']:
            _, items = self.retriever.retrieve(self.preference)
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





    