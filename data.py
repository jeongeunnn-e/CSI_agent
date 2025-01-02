
def load_dataset(filename):
    dataset = {'train':[], 'test':[]}
    for key in dataset:
        with open("%s-%s.txt"%(filename, key),'r') as infile:
            for line in infile:
                dataset[key].append(eval(line.strip('\n')))
    return dataset

class Data:
    def __init__(self, filename):
        self.data = self._load_data(filename)

    def _load_data(filename):
        data = []
        
        with open(filename,'r') as infile:
            for line in infile:
                temp = eval(line.strip('\n'))
                item_description = temp['item_description']
                budget = temp['budget']
                profile = temp['user_profile']
                data.append((item_description, budget, profile))
        
        return data