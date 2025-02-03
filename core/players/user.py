from core.prompt import *
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage

class Seeker:
    def __init__(self, user_data):
        self.model = ChatOpenAI(model='gpt-4o-mini')
        
        self.system_msg = self.__build_system_msg(user_data)
        self.init_utt = self._init_utt(user_data)

        user_data.print()
        

    def __build_system_msg(self, data):
        return  SystemMessage(
            content=user_system.format(
                general_preference=data.general_preference,
                target_needs=data.target_needs,
                target_category=data.target_category,
                purchase_reasons=data.purchase_reasons,
                budget_range=data.budget_range,
                decision_making_style=data.decision_making_style
            )
        )

    def generate_utterance(self, conversation_history):
        messages = [
            self.system_msg,
            *conversation_history,
            HumanMessage(content=user_prompt)
        ]
        output = self.model.generate([messages])
        response = output.generations[0][0].text
        return response

    def _init_utt(self, user_data):
        messages = [
            self.system_msg,
            HumanMessage(content=user_inital_prompt)
        ]
        output = self.model.generate([messages])
        response = output.generations[0][0].text
        print("User: ", response)
        return response
