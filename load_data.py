import json

def load_dataset(filename='data/clothing/css_data.json'):

    with open(filename, 'r') as f:
        json_data = json.load(f)

    meta_dict = json_data['meta_dict']
    interactions = json_data['interactions']
    user_profile = json_data['user_profile']

    dataset = [UserRequest(key, value) for key, value in user_profile.items()]
    return dataset, meta_dict, interactions


class UserRequest:

    def __init__(self, id, data):
        self.id = id

        # information for conversation
        self.general_preference = data['general_preference']
        self.purchase_reasons = data['purchase_reason']
        self.target_needs = data['target_needs']
        self.budget_range = data['budget']

        self.decision_making_style = data['decision_making_style']
        self.dialogue_openness = data['dialogue_openness']
        self.target_category = data['target_category']

    def print(self):
        print(f"ID: {self.id}")
        print(f"General Preference: {self.general_preference}")
        print(f"Decision Making Style: {self.decision_making_style}")
        print(f"Purchase Reasons: {self.purchase_reasons}")
        print(f"Target Needs: {self.target_needs}")
        print(f"Budget Range: {self.budget_range}")
        print(f"Target Category: {self.target_category}")
