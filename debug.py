import os
import pickle


def save_bad_id(bad_id):
    file_path = 'bad_id.pkl'
    data = []

    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            data = pickle.load(file)

    data.append(bad_id)

    with open(file_path, 'wb') as file:
        pickle.dump(data, file)
