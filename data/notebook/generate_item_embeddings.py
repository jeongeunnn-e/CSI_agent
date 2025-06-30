import argparse
import json
import os
import pdb
import pickle
import re
from collections import defaultdict
import tqdm
from sentence_transformers import SentenceTransformer
from torch.utils.data.dataset import Dataset
from transformers import AutoModel
import torch

torch.cuda.init()
print(torch.cuda.is_available())
torch.cuda.reset_peak_memory_stats(device=None)


class SentenceEmbeddingDataset(Dataset):
    def __init__(self, args):
        super().__init__()
        self.meta_dict = self.load_json(os.path.join(args.data_dir, 'meta_dict.json'))
        self.item_keys = list(self.meta_dict.keys())
        self.model = SentenceTransformer(f'sentence-transformers/{args.embedding_model}')
        # self.model.max_seq_length = 32768
        # self.model.tokenizer.padding_side = "right"

        self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        self.model.to(self.device)


    def __len__(self):
        return len(self.meta_dict)

    def load_json(self, file_path):
        with open(file_path, "r") as f:
            return json.load(f)

    def text_cleaning(self, text):
        text = re.sub(r'<.*?>', '', text)
        # text = re.sub(r'[^\w\s]', '', text)
        return text

    def add_eos(self, text):
        input_examples = text + self.model.tokenizer.eos_token
        return input_examples

    def __getitem__(self, idx):
        '''
        title / main_category + categories /features / description[0] / str(details): dict
        '''
        asin = self.item_keys[idx]
        meta = self.meta_dict[asin]
        text = 'This is a metadata of product information.'
        # keys = ['title', 'main_category', 'categories', 'features', 'description', 'details']
        text += f" Title: {self.meta_dict[asin]['title']}."
        # text += f" Main category: {self.meta_dict[asin]['main_category']}."
        # text += f" Categories: {str(self.meta_dict[asin]['categories'])}."
        # text += f" Features: {str(self.meta_dict[asin]['features'])}."
        text += f" Description: {str(self.meta_dict[asin]['description'])}."
        # text += f" Details: {str(self.meta_dict[asin]['details'])}."

        passages = self.text_cleaning(text)
        out_dict = defaultdict()
        out_dict['text'] = text
        passage_prefix = ""

        passage_embeddings = self.model.encode(passages)
        # passage_embeddings = self.model.encode(self.add_eos(passages), batch_size=1, normalize_embeddings=True)

        out_dict['embedding'] = passage_embeddings
        out_dict['asin'] = asin
        return out_dict


def get_embedding(dset):
    result = defaultdict()
    for idx in tqdm.tqdm(range(len(dset))):
        result[dset[idx]['asin']] = dset[idx]['embedding']
    return result


def save_embedding(save_path, result_dict):
    with open(save_path, 'wb') as fOut:
        pickle.dump(result_dict, fOut, protocol=pickle.HIGHEST_PROTOCOL)
    return print('saving embedding done!')


def create_embedding(args):
    dset = SentenceEmbeddingDataset(args)
    result = get_embedding(dset)
    save_embedding(args.save_path, result)
    print(f"Semantic Embedding is saved")


##########################################

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # domain = 'Clothing_Shoes_and_Jewelry'
    domain = 'electronics'
    parser.add_argument('--data_dir', type=str, default=f'../{domain}', help='')
    parser.add_argument('--embedding_model', type=str, default='sentence-t5-base', help='')
    parser.add_argument('--save_path', type=str, default=f'../{domain}/item_embedding_st5.pkl', help='')

    parser.parse_args()
    args = parser.parse_args()

    create_embedding(args)