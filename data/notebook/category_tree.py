import pdb
from typing import Dict, List
import json
import random


class TreeNode:
    def __init__(self, idx):
        self.idx = idx  # 현재 노드의 index
        self.children = {}  # 자식 노드들 (key: child index, value: TreeNode)
        self.items = []


class SampleTree:
    def __init__(self):
        self.root = TreeNode(None)  # category 저장

    def insert(self, path, id):
        current = self.root

        for level in path:
            current.items.append(id)
            if level not in current.children:
                current.children[level] = TreeNode(level)

            current = current.children[level]

    def search_children(self, path):
        current = self.root
        for level in path:
            if level in current.children:
                current = current.children[level]
            else:
                return None
        return list(current.children.keys())

    def search_id(self, path):
        current = self.root
        for level in path:
            if level in current.children:
                current = current.children[level]
            else:
                return None
        return current.items




import os
def load_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


domain = 'Clothing_Shoes_and_Jewelry'
data_dir = f'../clothing/'

meta_dict = load_json(os.path.join(data_dir, 'meta_dict.json'))
item_keys = list(meta_dict.keys())

categories = [(meta['categories'], meta['parent_asin']) for asin, meta in meta_dict.items()]

tree = SampleTree()
for (cate, id) in categories:
    tree.insert(cate, id)
