import json
import pickle
from scipy.spatial.distance import cosine
from core.prompt import *
from core.gen_models import OpenAIChatModel
from sentence_transformers import SentenceTransformer

class Item(object):
    def __init__(self, id, product_data:dict):
        self.id = id
        self.name = product_data['title']
        self.description = self.__format_product_data(product_data)

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
        self.model = SentenceTransformer("thenlper/gte-large")
        self.backbone_model = OpenAIChatModel('gpt-4o-mini')

    def retrieve(self, query):
        category_dict = self._chat_base_category_search(query)
        query_emb = self.model.encode(query)
        retrieve_item_ids = self._find_top_k_similar(category_dict, query_emb)
        retrieve_item_id = retrieve_item_ids[0]
        print("Retrieved item id:", retrieve_item_ids)
        return Item(retrieve_item_id, self.item_db[retrieve_item_id]), retrieve_item_ids
    
    def _find_top_k_similar(self, category_dict, query_embedding, k=5):
        
        similarities = [
            (key, 1 - cosine(query_embedding, category_dict[key]))
            for key in category_dict
        ]
        
        similarities = sorted(similarities, key=lambda x: x[1], reverse=True)
        top_k_ids = [key for key, _ in similarities[:k]]
        top_k_asins = [ self.id2asin[id] for id in top_k_ids ]
        return top_k_asins
    
    def _chat_base_category_search(self, query):

        message = [
            {'role':'system', 'content': chat_system_category_search},
            {'role': 'user', 'content': chat_assistant_category_search.format(search_query=query, category_list=str(self.category_list))}
        ]

        response = self.backbone_model.chat_generate(message)
        response = response[0]['generated_text']

        response = response.replace("'","").replace("*", "")

        try:
            searched_category = response.split("Selected category : ")[1]
        except IndexError:
            try:
                searched_category = response.split("Selected category: ")[1]
            except:
                searched_category = "Clothing"

        specific_keys = self.category_dict[searched_category]
        category_dict = {key: self.emb[key] for key in specific_keys if key in self.emb}

        return category_dict
        
    def _load_item_database(self):
        with open(f'data/{self.product_category}/meta_dict.json', 'r') as f:
            self.item_db = json.load(f)
        
        with open(f'data/{self.product_category}/item_embedding_gte.pkl', 'rb') as file:
            self.emb = pickle.load(file)

        with open(f'data/{self.product_category}/asin2id.json', 'r') as f:
            asin2id = json.load(f)
        self.id2asin = {value: key for key, value in asin2id.items()}
        
        with open(f'data/{self.product_category}/category_dict.json', 'r') as f:
            self.category_dict = json.load(f)
        self.category_list = list(self.category_dict.keys())