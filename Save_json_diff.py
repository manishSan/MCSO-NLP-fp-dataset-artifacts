# this file reads the base Squad/dev-v1.1-reformatted.json and Squad/dev-v1.1-adversarial-50.json files and creates 
# a diff file called Squad/dev-v1.1-adversarial-50-diff.json

# {
#     "id": "56be4db0acb8001400a502ec",
#     "title": "Super_Bowl_50",
#     "context": "That is correct! Super Bowl 50 was a milestone event in the history of the NFL. The Denver Broncos emerged as the champions by defeating the Carolina Panthers with a score of 24-10. The game took place on February 7, 2016, at Levi's Stadium in Santa Clara, California. To commemorate the 50th Super Bowl, the league incorporated various gold-themed initiatives, and for this particular edition, they temporarily suspended the tradition of using Roman numerals in the game's name, opting for the use of Arabic numerals instead.",
#     "question": "Which NFL team represented the AFC at Super Bowl 50?",
#     "answers": {
#         "text": [
#             "Denver Broncos",
#             "Denver Broncos",
#             "Denver Broncos"
#         ],
#         "answer_start": [
#             177,
#             177,
#             177
#         ]
#     }
# }

import json

def extract_base_contexts(base_file):

    with open(base_file, 'r') as file:
        squad_data = json.load(file)

    contexts = [obj['context'] for obj in squad_data]
    return set(contexts)

def extract_diff(base_file, adversarial_file):
    
    base_context = extract_base_contexts(base_file)

    with open(adversarial_file, 'r') as file:
        adv_data = json.load(file)

    diff_set = []
    same_set = []
    for obj in adv_data:
        if obj['context'] not in base_context:
            diff_set.append(obj)
        else:
            same_set.append(obj)

    return (diff_set, same_set)

def extract_and_write_diff(base_file, adversarial_file, diff_file, same_file):
    (diff_set, same_set) = extract_diff(base_file, adversarial_file)

    with open(diff_file, 'w') as file:
        json.dump(diff_set, file)

    with open(same_file, 'w') as file:
        json.dump(same_set, file)

# define the main entry point of the script
if __name__ == "__main__":
    # Prompt for a question
    base_file_path = './Squad/dev-v1.1-reformatted.json'
    adv_file_path = './Squad/dev-v1.1-adversarial-50.json'
    diff_file_path = './Squad/dev-v1.1-adversarial-50-diff.json'
    same_file_path = './Squad/dev-v1.1-adversarial-50-same.json'
    extract_and_write_diff(base_file_path, adv_file_path, diff_file_path, same_file_path)