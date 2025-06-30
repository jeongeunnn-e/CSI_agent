import json
import pdb
import pickle
import numpy as np
import os
from scipy.spatial.distance import cosine
from core.prompt import *
from core.players.tools.category_tree import get_tree
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage

import torch
from sentence_transformers import SentenceTransformer

class Item(object):
    def __init__(self, id, product_data: dict):
        self.id = id
        self.name = product_data['title']
        self.short_description = self.__format_product_data_short_ver(product_data)
        self.description = self.__format_product_data(product_data)

    def __format_product_data_short_ver(self, data):
        try:
            formatted_text = f"""Item Title: <{data.get('title', 'N/A')}> \n Item ID: {self.id} \n Price: ${data.get('price', 'N/A')} Category Path: {[cate.replace(',', '') for cate in data.get('categories', 'N/A')]} \n Description: {data.get('description', ['N/A'][0])[0]}"""
            return formatted_text
        except Exception as e:
            return str(data)

    def __format_product_data(self, data):
        try:
            formatted_text = f"""
            Item Title: <{data.get('title', 'N/A')}> \n
            Item ID: ({self.id}) \n
            [Price]: ${data.get('price', 'N/A')} \n
            Average Rating: {data.get('average_rating', 'N/A')} (Based on {data.get('rating_number', 'N/A')} reviews) \n
            Description: {data.get('description', ['N/A'])} \n
            Key Features:
            """
            for feature in data.get('features', []):
                formatted_text += f"- {feature} \n"
            formatted_text += "\nProduct Details: \n"
            for key, value in data.get('details', {}).items():
                formatted_text += f"- {key}: {value} \n"
            return formatted_text

        except Exception as e:
            return str(data)


class Retriever(object):

    def __init__(self, domain="clothing", model_name="sentence-transformers/sentence-t5-base", device="cuda"):
        self.product_category = domain
        self._load_item_database()
        self.root_category = 'Clothing, Shoes & Jewelry' if domain == 'clothing' else 'Electronics'
        self.device = device
        
        # Set custom cache directory
        # cache_dir = os.path.expanduser('/data/huggingface_cache')
        # os.makedirs(cache_dir, exist_ok=True)
        # os.environ['TRANSFORMERS_CACHE'] = cache_dir
        # os.environ['HF_HOME'] = cache_dir
        
        device = 'cuda:1' if torch.cuda.is_available() else 'cpu'
        self.model = SentenceTransformer(model_name, device=device)

    def retrieve(self, query, budget_range, category_path, category_tree):
        if type(budget_range) == str:
            import ast
            max_price = ast.literal_eval(budget_range)
            max_price = float(max_price[1]) if len(max_price) > 1 else float(max_price[0])
        else:
            max_price = float(budget_range[1])
        searched_category = category_path[-1] if len(category_path) > 0 else self.root_category

        specific_keys = category_tree.get_ids_by_path(category_path)
        category_dict = {key: self.emb[key] for key in specific_keys if key in self.emb}

        query_emb = self.model.encode([query])[0]
        retrieve_item_ids = self._find_top_k_similar(category_dict, query_emb, k=100)
        top_k_candidates = []
        for candidate in retrieve_item_ids:
            if max_price >0 and float(self.item_db[candidate]['price']) <= max_price:
                top_k_candidates.append(Item(candidate, self.item_db[candidate]))

        return searched_category, top_k_candidates[:3]

    def select_candidate(self, item_id, budget_range, category_path, category_tree):
        import ast
        if type(budget_range) == str:
            max_price = ast.literal_eval(budget_range)
            max_price = float(max_price[1])
        elif type(budget_range) == list:
            max_price = float(budget_range[1])
        else:
            max_price = float(budget_range[1])
        
        selected_emb = self.emb[item_id]
        specific_keys = category_tree.get_ids_by_path(category_path)
        category_dict = {key: self.emb[key] for key in specific_keys if key in self.emb}
        retrieve_item_ids = self._find_top_k_similar(category_dict, selected_emb, k=1000)
        top_k_candidates = []
        for candidate in retrieve_item_ids:
            if float(self.item_db[candidate]['price']) > max_price:
                top_k_candidates.append(Item(candidate, self.item_db[candidate]))

        return top_k_candidates

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
