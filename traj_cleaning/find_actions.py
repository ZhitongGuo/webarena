import os
import re
import json
import csv
import glob

# Directory paths for action and tree files
action_dir = '/Users/guozhitong/Desktop/WebArena/z_human-trajectories/cleaned_actions'
tree_dir = '/Users/guozhitong/Desktop/WebArena/z_human-trajectories/cleaned_htmls'

# Function to parse action file
def parse_action_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return data

# Function to parse tree file
def parse_tree_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

# Function to find the matching index in the tree
# def find_matching_index(action, tree):
#     temp_role = action.split('(')[0]
#     role_search = re.search(r'get_by_role\("([^"]+)"', action)

#     name_search = re.search(r'name="([^"]+)"', action)

#     if role_search is None or name_search is None:
#         return temp_role, None, None

#     role, name = role_search.group(1), name_search.group(1)
#     name = name.strip(' ')
#     tree_elements = re.findall(r'\[(\d+)\]\s+(\w+)\s+\'([^\']+)\'', tree)

#     for index, elem_role, elem_name in tree_elements:
#         if elem_role == role and elem_name == name:
#             # Construct a string representation of the element
#             element_str = f"[{index}] {elem_role} '{elem_name}'"
#             return temp_role, index, element_str

#     return temp_role, None, None

def remove_invalid_chars(input_string):
    pattern = r'\\ue60[0-9a-fA-F]'

    invalid_chars = re.findall(pattern, input_string)

    for char in invalid_chars:
        input_string.strip(char).strip(' ')

    return input_string.strip('\ue620 ').strip('\ue611 ').strip('\ue626 ').strip('\ue60f ').strip('\ue60b ').strip('\ue60c ').strip('\ue60d ').strip('\ue60a ').strip( '\ue609 ').strip('\ue608 ').strip('\ue607 ').strip('\ue606 ').strip('\ue605 ').strip('\ue604 ').strip('\ue603 ').strip('\ue602 ').strip('\ue601 ').strip('\ue600 ').strip('\ue60e ').strip('\ue60f ').strip('\ue60b ').strip('\ue60c ').strip('\ue60d ').strip('\ue60a ').strip( '\ue609 ').strip('\ue608 ').strip('\ue607 ').strip('\ue606 ').strip('\ue605 ').strip('\ue604 ').strip('\ue603 ').strip('\ue602 ').strip('\ue601 ').strip('\ue600 ').strip('\ue60e ')


def find_matching_index(action, tree):
    # Define regex patterns for different action types
    patterns = {
        'get_by_role': r'get_by_role\("([^"]+)",\s*name="([^"]+)"',
        'get_by_label': r'get_by_label\("([^"]+)"\)',
        'get_by_placeholder': r'get_by_placeholder\("([^"]+)"\)',
        'get_by_text': r'get_by_text\("([^"]+)"\)',
        'get_by_test_id': r'get_by_test_id\("([^"]+)"\)',
        'locator': r'locator\("([^"]+)"\)'
    }

    # Determine the action type and extract relevant parts
    for action_type, pattern in patterns.items():
        match = re.search(pattern, action)
        if match:
            if action_type == 'get_by_role':
                role, name = match.groups()
                name = remove_invalid_chars(name)
                criteria = lambda elem_role, elem_name: elem_role == role and name in elem_name
                break
            else:
                search_term = match.group(1)
                search_term = remove_invalid_chars(search_term)
                criteria = lambda elem_role, elem_name: search_term in elem_name
    
                break
    else:
        # No recognized action pattern found
        return action_type, None, None

    # Find matching element in the tree
    tree_elements = re.findall(r'\[(\d+)\]\s+(\w+)\s+(".*?"|\'.*?\')', tree) #re.findall(r'\[(\d+)\]\s+(\w+)\s+\'([^\']+)\'', tree)
    for index, elem_role, elem_name in tree_elements:
        if elem_role == 'textbox':
            print(elem_name)
        if criteria(elem_role, elem_name):
            element_str = f"[{index}] {elem_role} '{elem_name}'"
            return action_type, index, element_str

    return action_type, None, None


# Prepare CSV file
csv_file = open('output.csv', 'w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['Task ID', 'Step', 'Role', 'Action', 'Tree', 'Element Index', 'Element'])

# Processing files
for action_file in glob.glob(os.path.join(action_dir, '*.json')):
    task_id = os.path.basename(action_file).split('.')[0]
    actions = parse_action_file(action_file)

    for i, action in enumerate(actions):
        action = action[1]
        tree_file = os.path.join(tree_dir, f'{task_id}.trace_{i}.tree')
        if os.path.exists(tree_file):
            tree = parse_tree_file(tree_file)
            role, index, element_str = find_matching_index(action, tree)
            csv_writer.writerow([task_id, i, role, action, tree, index, element_str])

csv_file.close()
print("CSV file 'output.csv' has been created.")
