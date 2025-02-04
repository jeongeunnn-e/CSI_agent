from core.prompt import *
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage

class Seeker:
    def __init__(self, user_data, model_name):
        self.model = ChatOpenAI(model=model_name)
        
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
                decision_making_style=data.decision_making_style,
                dialogue_openness=data.dialogue_openness   
            )
        )

    def generate_utterance(self, conversation_history):
        messages = [
            self.system_msg,
            HumanMessage(content=user_prompt.format(conversation_history=self._conv_history_to_string(conversation_history)))
        ]
        output = self.model.generate([messages])
        response = output.generations[0][0].text
        return response


    def _init_utt(self, user_data):
        utt =  f"I am looking for {user_data.target_category[-3]} under ${user_data.budget_range[1]}."
        print("\033[1;34mUser:\033[0m", utt)
        return utt
    
        messages = [
            self.system_msg,
            HumanMessage(content=user_inital_prompt)
        ]
        output = self.model.generate([messages])
        response = output.generations[0][0].text
        
        return response


    def _conv_history_to_string(self, conversation_history):
        serializable_history = [
            {
                "role": "System" if isinstance(msg, SystemMessage) else "Seeker" if isinstance(msg, HumanMessage) else "Recommender",
                "content": msg.content
            }
            for msg in conversation_history
        ]
        
        resp = "\n".join([f"{msg['role']}: {msg['content']}" for msg in serializable_history])
        return resp