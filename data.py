import json

def load_dataset(filename='data/persona_temp0.7_interactions.json'):
    with open(filename, 'r') as f:
        json_data = json.load(f)
    
    data = [ UserRequest(key, value) for key, value in json_data.items() ]
    return data


class UserRequest:
    def __init__(self, id, data):
        self.id = id

        # information for conversation
        self.persona = data['persona_description']
        self.profile = data['user_profile']
        self.target_category = data['target_category']
        self.target_budget = data['target_price']

        # GT for the recommendation task
        self.pos_ids = data['target']