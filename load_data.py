import json

def load_dataset(filename='data/clothing/user_data_0120.json'):
    with open(filename, 'r') as f:
        json_data = json.load(f)
    
    # bad_ids = ['AHZW2TZHT7YOI4VPVVVIS4ZX7WHQ']
    # for bad_id in bad_ids:
    #     del json_data[bad_id]

    data = [ UserRequest(key, value) for key, value in json_data.items() ]
    return data


class UserRequest:

    def __init__(self, id, data):
        self.id = id

        # information for conversation
        self.general_preference = data['general_preference'] # self._format_preference_dict(data['general_preference'])
        self.decision_making_style = data['decision_making_style'] # data['reasoning']

        self.purchase_reasons = [ item["purchase_reasons"] for key, item in data["target_needs"].items() ]
        self.target_needs = [ item["target_needs"] for key, item in data["target_needs"].items() ]
        self.budget_range = data['target_price'][0], data['target_price'][-1]

        # GT for the recommendation task
        self.target_category = data['target_category']
        self.target_ids = data['targets']


    def _format_preference_dict(self, preference_dict):

        label_mapping = {
            "frequently_purchased_categories": "Frequently Purchased Categories",
            "preferred_brands": "Preferred Brands",
            "colors": "Favorite Colors",
            "key_attributes": "Key Attributes",
            "likes": "Likes",
            "dislikes": "Dislikes",
        }

        general_preference = preference_dict.get("general_preference", {})
        output = [
            f"{label_mapping[key]}:\n" + "\n".join(f"  - {item}" for item in general_preference[key])
            for key in label_mapping if key in general_preference
        ]

        return "\n\n".join(output)

    def print(self):
        print(f"ID: {self.id}")
        print(f"General Preference: {self.general_preference}")
        print(f"Decision Making Style: {self.decision_making_style}")
        print(f"Purchase Reasons: {self.purchase_reasons}")
        print(f"Target Needs: {self.target_needs}")
        print(f"Budget Range: {self.budget_range}")
        print(f"Target Category: {self.target_category}")
        print(f"Target IDs: {self.target_ids}")