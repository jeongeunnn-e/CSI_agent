import json
import pickle
from scipy.spatial.distance import cosine
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
        self._load_item_database()
        self.model = SentenceTransformer('sentence-transformers/sentence-t5-base')

    def retrieve(self, query):
        query_emb = self.model.encode(query)
        retrieve_item_id, _ = self.find_most_similar(query_emb)
        return Item(retrieve_item_id, self.item_db[self.id2asin[retrieve_item_id]])
    
    def find_most_similar(self, query_embedding):
        most_similar_id = max(self.emb, key=lambda key: 1 - cosine(query_embedding, self.emb[key]))
        highest_similarity = 1 - cosine(query_embedding, self.emb[most_similar_id])

        return most_similar_id, highest_similarity

    def _load_item_database(self):
        with open('data/meta_dict.json', 'r') as f:
            self.item_db = json.load(f)
        
        with open('data/item_embedding.pkl', 'rb') as file:
            self.emb = pickle.load(file)

        with open('data/asin2id.json', 'r') as f:
            asin2id = json.load(f)
        self.id2asin = {value: key for key, value in asin2id.items()}
