import json
from core.prompt import *
from baselines.prompt import *
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage


class ReAct_Async:
    def __init__(self, tool, model_name):

        self.model = ChatOpenAI(model=model_name, temperature=0.7)
        self.tool = tool
        self.thoughts = []
        self.category_path = ['Clothing Shoes & Jewelry']
        self.persuasion_strategies = []
        self.selected = []
        self.candidates = []


    async def generate_utterance(self, conversation_history):

        conv_hist = self._conv_history_to_string(conversation_history)

        messages = [
            SystemMessage(content=naive_react.format(conversation_history=self._conv_history_with_thoughts(conversation_history))),
        ]

        output = await self.model.agenerate([messages], response_format={"type": "json_object"})
        response = output.generations[0][0].text
        # response = response.strip("'```json").strip("```'").replace("{{", "{").replace("}}", "}").replace("None", "null")
        response = json.loads(response)

        thought = response['Thoughts']
        action = response['Action']
        output = response['Output'] if 'Output' in response else None

        self.thoughts.append(response)
        
        if action in ['Category Narrowing']:
            messages = [
                SystemMessage(content=chat_system_category_search.format(preference=thought,
                                                                            category_list=self.tool.category_search(self.category_path)))
            ]

            output = await self.model.agenerate([messages])
            response = output.generations[0][0].text
            return response

        elif action in ['Preference Probing']:
            messages = [
                SystemMessage(content=chat_system_question_generation.format(conversation_history=conv_hist,
                                                                             user_preference=""))
            ]
            output = await self.model.agenerate([messages])
            response = output.generations[0][0].text
            return response
        
        elif action in ['Persuasion']:
            try:
                budget_range = output['budget_range'].replace('$', '').replace(' - ',',').replace(' to ',',')
                candidates = self.tool.retriever.select_candidate(output['item ID'], budget_range, self.category_path, self.tool.category_tree)
                self.candidates.append(candidates[0])
                messages = [
                    SystemMessage(content=naive_persuasion_system.format(item_info=self.selected[-1].description,
                                                                        candidate_info=candidates[0].description)),
                    *conversation_history,
                    SystemMessage(content=naive_persuasion_user)
                ]
            except:
                messages = [
                    SystemMessage(content=naive_persuasion_system.format(item_info=self.selected[-1].description,
                                                                        candidate_info=None)),
                    * conversation_history,
                    SystemMessage(content=naive_persuasion_user)
                ]
            output = await self.model.agenerate([messages])
            response = output.generations[0][0].text
            response = response.replace("{{", "{").replace("}}", "}")
            response = json.loads(response)
            self.persuasion_strategies.append(response['strategy'])
            return response['sentence']
        
        else:
            if 'category_path' in output:
                self.category_path = self.tool.category_update(self.category_path, output['category_path'])
            else:
                self.category_path = ['Clothing Shoes & Jewelry']
            
            if isinstance(output['budget_range'], str):
                budget_range = output['budget_range'].replace('$', '').replace(' - ',',').replace(' to ',',')
            else:
                budget_range = output['budget_range']
            _, items = self.tool.retriever.retrieve(thought, budget_range, self.category_path, self.tool.category_tree)

            if len(items) == 0:
                return "I'm sorry, I couldn't find any items that match your preferences. Can you try again with different preferences?"
            
            self.selected.append(items[0])
            items_info = [item.short_description for item in items]

            utt = "Here are some items that you might like: \n"
            for i, item in enumerate(items_info):
                utt += f"{i + 1}. {item}\n"

            return utt
        
        
    def _conv_history_to_string(self, conversation_history):
        serializable_history = [{"role": "System" if isinstance(msg, SystemMessage) else "Seeker" if isinstance(msg, HumanMessage) else "Recommender", "content": msg.content} for msg in conversation_history]

        resp = "\n".join([f"{msg['role']}: {msg['content']}" for msg in serializable_history])
        return resp
    
    def _conv_history_with_thoughts(self, conversation_history):
        turn = len(conversation_history)//2 
        
        resp = ""
        for idx in range(turn):
            resp += f"Seeker: {conversation_history[2*idx].content}\n"
            resp += f"System: {conversation_history[2*idx+1].content}\n"
            resp += f"Thoughts: {self.thoughts[idx]['Thoughts']}\n"
            resp += f"Action: {self.thoughts[idx]['Action']}\n"

        resp += f"Seeker: {conversation_history[-1].content}\n"
        return resp


class PCCRS_Async:
    def __init__(self, tool, model_name):

        self.model = ChatOpenAI(model=model_name, temperature=0.7)
        self.tool = tool
        self.thoughts = []
        self.category_path = ['Clothing Shoes & Jewelry']
        self.persuasion_strategies = []
        self.selected = []
        self.candidates = []


    async def generate_utterance(self, conversation_history):

        conv_hist = self._conv_history_to_string(conversation_history)

        response = await self.generate(pc_crs_retrieval.format(conversation_history=conv_hist))
        if isinstance(response['budget_range'], str):
            budget_range = response['budget_range'].replace('$', '').replace(' - ',',').replace(' to ',',')
        if isinstance(response['budget_range'], list):
            if isinstance(response['budget_range'][0], str):
                budget_range = [ tmp.replace('$', '') for tmp in response['budget_range'] ]
            else:
                budget_range = response['budget_range']
        _, items = self.tool.retriever.retrieve(conv_hist, budget_range, self.category_path, self.tool.category_tree)

        if len(items) == 0:
            return "I'm sorry, I couldn't find any items that match your preferences. Can you try again with different preferences?"
        
        self.selected.append(items[0])
        candidates = self.tool.retriever.select_candidate(self.selected[-1].id, budget_range, self.category_path, self.tool.category_tree)
        if len(candidates) > 0:
            self.candidates.append(candidates[0])

        response = await self.generate(pc_crs_strategy_selection.format(conversation_history=conv_hist))
        strategies = response['strategies']
        self.persuasion_strategies.append(strategies)

        if 'Anchoring' not in strategies:
            strategies = [strategies[0]]

        persuasion_strategy_prompt = ""
        for strategy in strategies:
            persuasion_strategy_prompt += strategy_prompt_dict[strategy] + "\n"

        response = await self.generate(pc_crs_persuasion.format(conversation_history=conv_hist, 
                                                          strategy=persuasion_strategy_prompt,
                                                          first_item_info=self.selected[-1].description,
                                                          second_item_info=self.candidates[-1].description if len(candidates) > 0 else ""))
        persuasion_utt_1 = response['response 1']
        persuasion_utt_2 = response['response 2']
        persuasion_utt = "You might like these items : " + persuasion_utt_1 + "\n" + persuasion_utt_2


        response = await self.generate(pc_crs_factcheck.format(sys_utt=persuasion_utt,
                                                         first_item_info=self.selected[-1].description,
                                                         second_item_info=self.candidates[-1].description if len(candidates) > 0 else ""))
        if response['Truthfulness'] == 'True':
            return persuasion_utt

        response = await self.generate(pc_crs_refinement.format(conversation_history=conv_hist,
                                                            first_item_info=self.selected[-1].description,
                                                            second_item_info=self.candidates[-1].description if len(candidates) > 0 else "",
                                                            sys_utt=persuasion_utt,
                                                            critique=response['Evidence'],
                                                            strategy=persuasion_strategy_prompt))

        return response['response']


    async def generate(self, system_prompt):
        messages = [
            SystemMessage(content=system_prompt),
        ]

        response = await self.model.agenerate([messages], response_format={"type": "json_object"})
        response = response.generations[0][0].text
        response = json.loads(response)
        return response


    def _conv_history_to_string(self, conversation_history):
        serializable_history = [{"role": "System" if isinstance(msg, SystemMessage) else "Seeker" if isinstance(msg, HumanMessage) else "Recommender", "content": msg.content} for msg in conversation_history]

        resp = "\n".join([f"{msg['role']}: {msg['content']}" for msg in serializable_history])
        return resp