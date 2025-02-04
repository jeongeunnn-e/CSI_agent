import json
import pickle
import numpy as np
from scipy.spatial.distance import cosine
from core.prompt import *
from core.players.tools.category_tree import get_tree
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage

from sentence_transformers import SentenceTransformer

class Item(object):
    def __init__(self, id, product_data:dict):
        self.id = id
        self.name = product_data['title']
        self.short_description = self.__format_product_data_short_ver(product_data)
        self.description = self.__format_product_data(product_data)

    def __format_product_data_short_ver(self, data):
        try:
            formatted_text = f"""
            Product Name: {data.get('title', 'N/A')} 
            Item ID: {self.id}
            Description:
            {data.get('description', ['N/A'])[0]}
            """
            return formatted_text
        except Exception as e:
            return str(data)

    def __format_product_data(self, data):
        try:
            formatted_text = f"""
            Product Name: {data.get('title', 'N/A')}
            Main Category: {data.get('main_category', 'N/A')}
            Store: {data.get('store', 'N/A')}

            [Price]: ${data.get('price', 'N/A')}
            Average Rating: {data.get('average_rating', 'N/A')} (Based on {data.get('rating_number', 'N/A')} reviews)

            Description:
            {data.get('description', ['N/A'])[0]}

            Key Features:
            """
            for feature in data.get('features', []):
                formatted_text += f"- {feature}\n"

            formatted_text += "\nCategories:\n"
            formatted_text += ", ".join(data.get('categories', ['N/A'])) + "\n"

            formatted_text += "\nProduct Details:\n"
            for key, value in data.get('details', {}).items():
                formatted_text += f"- {key}: {value}\n"

            return formatted_text
        except Exception as e:
            return str(data)
        
class Retriever(object):

    def __init__(self):

        self.product_category = "clothing"
        self._load_item_database()

        self.model = SentenceTransformer(f'sentence-transformers/sentence-t5-base')
        self.model.tokenizer.padding_side = "right"
        self.backbone_model = ChatOpenAI(model='gpt-4o-mini')


    def retrieve(self, query, category_path, category_tree):

        searched_category = category_path[-1] if len(category_path) > 0 else 'Clothing, Shoes & Jewelry'

        specific_keys = category_tree.search_id(category_path)
        category_dict = {key: self.emb[key] for key in specific_keys if key in self.emb}

        # task_name_to_instruct = {"example": "Given a query, retrieve product that matches the attributes.",}
        # query_prefix = "Instruct: "+task_name_to_instruct["example"]+"\nQuery: "
        # query_emb = self.model.encode(self._add_eos([query]), batch_size=1, prompt=query_prefix, normalize_embeddings=True)

        query_emb = self.model.encode(query)
        retrieve_item_ids = self._find_top_k_similar(category_dict, query_emb)
        retrieve_items = [ Item(retrieve_item_id, self.item_db[retrieve_item_id]) for retrieve_item_id in retrieve_item_ids ]
        
        return searched_category, retrieve_items


    def _add_eos(self, input_examples):
        input_examples = [input_example + self.model.tokenizer.eos_token for input_example in input_examples]
        return input_examples


    def _find_top_k_similar(self, category_dict, query_embedding, k=5):

        ids = list(category_dict.keys())
        embeddings = np.array([category_dict[key] for key in ids])
        scores = (query_embedding @ embeddings.T).flatten()  
        sorted_indices = np.argsort(scores)[::-1]
        sorted_scores = scores[sorted_indices]
        sorted_ids = [ids[idx] for idx in sorted_indices]        
        top_k_indices = sorted_indices[:k]
        top_k_ids = [ids[idx] for idx in top_k_indices]
        
        return top_k_ids
    

    def retrieve_by_id(self, asin):
        return Item(asin, self.item_db[asin])
        
    def _load_item_database(self):

        with open(f'data/{self.product_category}/item_embedding_st5.pkl', 'rb') as file:
            self.emb = pickle.load(file)

        with open(f'data/{self.product_category}/css_data.json', 'r') as f:
            css_data = json.load(f)

        self.item_db = css_data['meta_dict']

        