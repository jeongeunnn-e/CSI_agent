import json
import random

class Item(object):
    def __init__(self, product_data:dict):
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
        self.item_db = self._load_item_database()

    def retrieve(self, query):
        return Item(random.choice(self.item_db))
    
    def _load_item_database(self, file_path: str = 'core/item_database.jsonl'):
        with open(file_path, 'r') as f:
            return [json.loads(line) for line in f if line.strip()]