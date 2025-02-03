import pdb
from typing import Dict, List
import json
import random


class TreeNode:
    def __init__(self, idx):
        self.idx = idx 
        self.children = {} 
        self.items = []


class SampleTree:
    def __init__(self):
        self.root = TreeNode(None)  # category 저장

    def insert(self, path, id):
        current = self.root
        current.items.append(id)

        for level in path:
            if level not in current.children:
                current.children[level] = TreeNode(level)

            current = current.children[level]
            current.items.append(id)

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
    
    def get_init_detph_3_paths(self):
        routes = []

        def dfs(node, path, depth):
            if depth == 3:
                routes.append(" > ".join(path[1:]))
                return

            for child_name, child_node in node.children.items():
                dfs(child_node, path + [child_name], depth + 1)

        dfs(self.root, [], 0)
        return routes


def get_tree():

    import os
    def load_json(file_path):
        with open(file_path, "r") as f:
            return json.load(f)


    domain = 'Clothing_Shoes_and_Jewelry'
    data_dir = '/work/convagent/CSA/data/clothing'

    meta_dict = load_json(os.path.join(data_dir, 'meta_dict.json'))
    item_keys = list(meta_dict.keys())

    categories = [(meta['categories'], meta['parent_asin']) for asin, meta in meta_dict.items()]


    tree = SampleTree()
    for (cate, id) in categories:
        tree.insert(cate, id)

    return tree


