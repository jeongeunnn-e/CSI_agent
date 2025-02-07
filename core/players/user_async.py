from core.prompt import *
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage


class Seeker_async:
    def __init__(self, user_data, model_name):
        self.model = ChatOpenAI(model=model_name, temperature=0)
        self.openness = user_data.dialogue_openness

        self.system_msg = self.__build_system_msg(user_data)
        self.init_utt = None

        # user_data.print()

    def __build_system_msg(self, data):
        return SystemMessage(
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

    async def generate_utterance(self, conversation_history):
        messages = [
            self.system_msg,
            SystemMessage(content=user_prompt.format(conversation_history=self._conv_history_to_string(conversation_history), dialogue_openness=self.openness))
        ]
        output = await self.model.agenerate([messages])
        response = output.generations[0][0].text
        return response

    async def init_utt_async(self, user_data):
        """비동기적으로 초기 발화 생성"""
        messages = [
            self.system_msg,
            SystemMessage(content=user_inital_prompt.format(dialogue_openness=user_data.dialogue_openness))
        ]
        output = await self.model.agenerate([messages])  # 비동기 호출
        response = output.generations[0][0].text
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
