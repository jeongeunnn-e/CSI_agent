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
                routes.append(path[1:])
                return

            for child_name, child_node in node.children.items():
                dfs(child_node, path + [child_name], depth + 1)

        dfs(self.root, [], 0)
        return routes

    def get_depth_3_paths_from(self, start_node):

        routes = []

        def find_node(node, target_name):
            if node.idx == target_name:
                return node
            for child in node.children.values():
                found = find_node(child, target_name)
                if found:
                    return found
            return None

        def dfs(node, path, depth):
            if depth == 3:
                routes.append(" > ".join(path[1:]))
                return
            for child_name, child_node in node.children.items():
                dfs(child_node, path + [child_name], depth + 1)

        start_node_ref = find_node(self.root, start_node)

        if start_node_ref:
            dfs(start_node_ref, [start_node], 1)
        else:
            print(f"Node '{start_node}' not found in the tree.")

        return routes

    def check_existing_path(self, path):
        def find_start_node(node, level):
            if level in node.children:
                return node.children[level]
            # for child in node.children.values():
            #     found = find_start_node(child, level)
            #     if found:
            #         return found
            return None

        start_node = find_start_node(self.root, path[0])

        if not start_node:
            return []

        current = start_node
        valid_path = [path[0]]

        for level in path[1:]:
            if level in current.children:
                valid_path.append(level)
                current = current.children[level]
            else:
                break

        return valid_path

    def get_paths_to_node(self, node_name):
        paths = []

        def dfs(node, path):
            if node.idx == node_name:
                paths.append(path[:])  # Store a copy of the path

            for child_name, child_node in node.children.items():
                dfs(child_node, path + [child_name])

        dfs(self.root, [])
        return paths

    def get_depth_3_paths_from_path(self, start_path):

        routes = []

        def find_node_by_path(node, path):
            """ Traverse the tree along the given path and return the target node. """
            current = node
            for level in path:
                if level in current.children:
                    current = current.children[level]
                else:
                    return None  # Path does not exist
            return current

        def dfs(node, path, depth):
            """ Perform DFS up to depth 2 from the given node, including leaf nodes. """
            if depth == 2:  # Stop at depth 2 or if it's a leaf
                routes.append(path[-2:])  # Add last 2 elements
                return
            if not node.children:
                routes.append(path[-1])
                return
            for child_name, child_node in node.children.items():
                dfs(child_node, path + [child_name], depth + 1)

        # Find the last node in the given path
        start_node_ref = find_node_by_path(self.root, start_path)

        if start_node_ref:
            dfs(start_node_ref, start_path, 0)  # Start DFS from the last node in path
        else:
            print(f"Path '{' > '.join(start_path)}' not found in the tree.")

        return routes

    def get_ids_by_path(self, category_path):

        def find_node_by_path(node, path):
            """ Traverse the tree along the given path and return the target node. """
            current = node
            for level in path:
                if level in current.children:
                    current = current.children[level]
                else:
                    return None  # Path does not exist
            return current

        # Find the target node for the given path
        target_node = find_node_by_path(self.root, category_path)

        # Return item IDs if the node exists, else return an empty list
        return target_node.items if target_node else []


def get_tree(path):
    import os
    def load_json(file_path):
        with open(file_path, "r") as f:
            return json.load(f)

    data = load_json(path)
    meta_dict = data['meta_dict']

    categories = [([cate.replace(',', '') for cate in meta['categories'][:5]], meta['parent_asin']) for asin, meta in meta_dict.items()]

    tree = SampleTree()
    for (cate, id) in categories:
        tree.insert(cate, id)

    return tree
