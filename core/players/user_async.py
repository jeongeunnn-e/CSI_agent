from core.prompt import *
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
import os


class Seeker_async:
    def __init__(self, user_data, model_name, temperature):
        # Get API key from environment variable or use a default one
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it using: export OPENAI_API_KEY='your-api-key-here'")
            
        self.model = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=api_key
        )
        self.openness = user_data.dialogue_openness
        self.decision = user_data.decision_making_style
        self.openness_desc = f'{self.openness} : {user_data.openness_description[self.openness]}'.replace('Less Active','Neutral')
        self.decision_desc = f'{self.decision} : {user_data.decision_description[self.decision]}'

        self.system_msg = self.__build_system_msg(user_data)
        self.init_utt = None
        self.data = user_data
        # user_data.print()

    def __build_system_msg(self, data):
        return SystemMessage(
            content=user_system.format(
                general_preference=data.general_preference,
                target_needs=data.target_needs,
                target_category=data.target_category,
                purchase_reasons=data.purchase_reasons,
                budget_range=data.budget_range,
                decision_making_style=self.decision_desc,
                dialogue_openness=self.openness_desc
            )
        )

    async def generate_utterance(self, conversation_history):
        messages = [
            self.system_msg,
            SystemMessage(content=user_prompt.format(conversation_history=self._conv_history_to_string(conversation_history), dialogue_openness=self.openness_desc))
        ]
        output = await self.model.agenerate([messages])
        response = output.generations[0][0].text

        return response

    async def init_utt_async(self, data):
        messages = [
            SystemMessage(content=user_initial_prompt.format(target_needs=data.target_needs,
                                                             dialogue_openness=self.openness_desc))
        ]
        output = await self.model.agenerate([messages])  # 비동기 호출
        response = output.generations[0][0].text
        response += f" within my expected price range: {data.budget_range}"
        self.init_utt = response  # 생성된 응답을 저장
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
