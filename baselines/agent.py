import json
import debug
from core.prompt import *
from baselines.prompt import *
from core.players.tools.retriever import Retriever
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage


class ReAct:
    def __init__(self, tool, model_name):

        self.model = ChatOpenAI(model=model_name, temperature=0.7)
        self.tool = tool
        self.y = [ None, None]
        self.thoughts = []
        self.category_path = ['Clothing Shoes & Jewelry']
        self.persuasion_strategies = []
        self.selected = []
        self.candidates = []


    def generate_utterance(self, conversation_history):

        messages = [
            SystemMessage(content=naive_react_system),
            *conversation_history,
            SystemMessage(content=naive_react_user)
        ]

        output = self.model.generate([messages])
        response = output.generations[0][0].text
        response = response.strip("'```json").strip("```'")
        response = response.replace("{{", "{").replace("}}", "}").replace("None", "null")
        print(response)
        response = json.loads(response)

        thought = response['Thoughts']
        action = response['Action']
        output = response['Output']

        self.thoughts.append(response)

        if action in ['Category Narrowing']:
            messages = [
                SystemMessage(content=chat_system_category_search.format(preference=output['preference'],
                                                                            category_list=self.tool.category_search(self.category_path)))
            ]

            output = self.model.generate([messages])
            response = output.generations[0][0].text
            return response

        elif action in ['Preference Probing']:
            messages = [
                SystemMessage(content=chat_system_question_generation.format(conversation_history=conversation_history,
                                                                             user_preference=""))
            ]
            output = self.model.generate([messages])
            response = output.generations[0][0].text
            return response

        elif action in ['Retrieve']:
            if 'category_path' in output:
                self.category_path = self.tool.category_update(self.category_path, output['category_path'])
            else:
                self.category_path = ['Clothing Shoes & Jewelry']

            budget_range = output['budget_range'].replace('$', '').replace(' - ',',').replace(' to ',',')
            _, items = self.tool.retriever.retrieve(output['search_query'], budget_range, self.category_path, self.tool.category_tree)

            if len(items) == 0:
                return "I'm sorry, I couldn't find any items that match your preferences. Can you try again with different preferences?"
            
            self.selected.append(items[0])
            items_info = [item.short_description for item in items]

            utt = "Here are some items that you might like: \n"
            for i, item in enumerate(items_info):
                utt += f"{i + 1}. {item}\n"

            return utt
        
        elif action in ['Persuasion']:
            try:
                budget_range = output['budget_range'].replace('$', '').replace(' - ',',').replace(' to ',',')
                candidates = self.tool.retriever.select_candidate(output['item ID'], budget_range, self.category_path, self.tool.category_tree)
                print("\033[1;33mCandidate: \033[0m", candidates[0].id)
                self.candidates.append(candidates[0])
                messages = [
                    SystemMessage(content=naive_persuasion_system.format(item_info=self.selected[-1].description,
                                                                        candidate_info=candidates[0].description)),
                    *conversation_history,
                    SystemMessage(content=naive_persuasion_user)
                ]
            except:
                print('No candidate exists')

                messages = [
                    SystemMessage(content=naive_persuasion_system.format(item_info=self.selected[-1].description,
                                                                        candidate_info=None)),
                    * conversation_history,
                    SystemMessage(content=naive_persuasion_user)
                ]
            output = self.model.generate([messages])
            response = output.generations[0][0].text
            response = response.replace("{{", "{").replace("}}", "}")
            print(response, "\n")
            response = json.loads(response)
            self.persuasion_strategies.append(response['strategy'])
            return response['sentence']


class PCCRS:
    def __init__(self, tool, model_name):

        self.model = ChatOpenAI(model=model_name, temperature=0.7)
        self.tool = tool
        self.y = [ None, None]
        self.thoughts = []
        self.category_path = ['Clothing Shoes & Jewelry']
        self.persuasion_strategies = []
        self.selected = []
        self.candidates = []


    def generate_utterance(self, conversation_history):

        conv_hist = self._conv_history_to_string(conversation_history)

        response = self.generate(pc_crs_retrieval.format(conversation_history=conv_hist))
        budget_range = response['budget_range'].replace('$', '').replace(' - ',',').replace(' to ',',')
        _, items = self.tool.retriever.retrieve(conv_hist, budget_range, self.category_path, self.tool.category_tree)

        if len(items) == 0:
            return "I'm sorry, I couldn't find any items that match your preferences. Can you try again with different preferences?"
        
        self.selected.append(items[0])
        candidates = self.tool.retriever.select_candidate(self.selected[-1].id, budget_range, self.category_path, self.tool.category_tree)
        self.candidates.append(candidates[0])

        response = self.generate(pc_crs_strategy_selection.format(conversation_history=conv_hist))
        strategies = response['strategies']

        if 'Anchoring' not in strategies:
            strategies = [strategies[0]]

        persuasion_strategy_prompt = ""
        for strategy in strategies:
            persuasion_strategy_prompt += strategy_prompt_dict[strategy] + "\n"

        response = self.generate(pc_crs_persuasion.format(conversation_history=conv_hist, 
                                                          strategy=persuasion_strategy_prompt,
                                                          first_item_info=self.selected[-1].description,
                                                          second_item_info=self.y[1].description))
        persuasion_utt_1 = response['response 1']
        persuasion_utt_2 = response['response 2']
        persuasion_utt = persuasion_utt_1 + "\n" + persuasion_utt_2

        response = self.generate(pc_crs_factcheck.format(sys_utt=persuasion_utt,
                                                         item_info=self.selected[-1].description + "\n" + self.y[1].description))
        if response['Truthfulness'] == 'True':
            return persuasion_utt

        response = self.generate(pc_crs_refinement.format(conversation_history=conv_hist,
                                                            item_info=self.selected[-1].description + "\n" + self.y[1].description,
                                                            sys_utt=persuasion_utt,
                                                            critique=response['Evidence'],
                                                            strategy=persuasion_strategy_prompt))

        return response['response']


    def generate(self, system_prompt):
        messages = [
            SystemMessage(content=system_prompt),
        ]

        response = self.model.generate([messages]).generations[0][0].text
        response = response[response.index('{'):]
        print(response)
        response = json.loads(response)
        return response


    def _conv_history_to_string(self, conversation_history):
        serializable_history = [{"role": "System" if isinstance(msg, SystemMessage) else "Seeker" if isinstance(msg, HumanMessage) else "Recommender", "content": msg.content} for msg in conversation_history]

        resp = "\n".join([f"{msg['role']}: {msg['content']}" for msg in serializable_history])
        return resp