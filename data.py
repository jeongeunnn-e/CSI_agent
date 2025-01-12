import json

def load_dataset(filename='data/clothing/user__needs_w_target.json'):
    with open(filename, 'r') as f:
        json_data = json.load(f)
    
    data = [ UserRequest(key, value) for key, value in json_data.items() ]
    return data


class UserRequest:
    def __init__(self, id, data):
        self.id = id

        # information for conversation
        self.user_profile = data['user_profile']
        self.user_personality = data['big_five_personality']
        self.decision_making_style = data['decision_making_style']
        self.target_needs = data['review']

        # GT for the recommendation task
        self.pos_ids = data['target']