import json
import random
from openai import OpenAI

def modify_sentence(sentence):
    # TODO: Implement sentence modification logic here
    # This could involve calling an external NLP service, like an AI model, to paraphrase sentences.
    return sentence

def introduce_noise(sentence_list):
    # TODO: Implement logic to introduce noise sentences here
    return sentence_list

import requests

# GPT_MODEL = "gpt-4-1106-preview"
GPT_MODEL = "gpt-3.5-turbo-16k-0613"
seed = 42
API_KEY = "---"
client = OpenAI(api_key=API_KEY)
def call_chatgpt(prompt, context, max_tokens=1000):
    """
    Makes an API call to a ChatGPT-like model.

    :param prompt: The input text prompt to send to the model.
    :param max_tokens: The maximum number of tokens to generate in the response.
    :return: The model's response as a string.
    """
    messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": context},
        ]
    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=messages,
        seed=seed,
        max_tokens=max_tokens,
        temperature=0.7,
        # response_json=True,
        # response_format='{ "type": "json_object" }'
    )
    if 'error' in response: 
        print(response['error'])
        return None 
    else: 
        print("ChatGPT request successful")
        return response.choices[0].message.content.strip()

    # # The URL of the API endpoint
    # api_url = "https://api.openai.com/v1/engines/davinci-codex/completions"

    # # Your API key for authentication
    # api_key = "your-api-key"

    # # The headers for the HTTP request
    # headers = {
    #     "Authorization": f"Bearer {api_key}",
    #     "Content-Type": "application/json",
    # }

    # # The JSON body of the request
    # payload = {
    #     "prompt": prompt,
    #     "max_tokens": max_tokens
    # }

    # # Make the POST request
    # response = requests.post(api_url, headers=headers, json=payload)

    # # Check if the request was successful
    # if response.status_code == 200:
    #     # Parse the response content
    #     response_json = response.json()
    #     # Extract the generated text
    #     return response_json["choices"][0]["text"].strip()
    # else:
    #     # If the request was not successful, print the error
    #     return f"Error: {response.status_code}, {response.text}"

def create_adversarial_context(context, percentage=40):
    # use call_GPT to generate adversarial context
    prompt = "Paraphrase the following with following Augmentation." \
                "1. Add contractions and negation words"\
                "2. Add synonyms and antonyms"\
                "3. Add noise - sentences that are not related to paragraph but they could confuse model"\
                "Make sure the meaning of sentences and overall meaning and sentiment doesn't change."\
                "Keep the length of the generated response almost the same as the input context"
                # "Always return a valid JSON in response"
    
    # prompt = prompt + "\n" + context
    
    adversarial_prompt = call_chatgpt(prompt, context)
    return adversarial_prompt

def create_adversarial_contexts(contexts, percentage=20):
    adversarial_contexts = []
    print('Contexts to update - ', len(contexts))
    for context in contexts:
        ad_context = create_adversarial_context(context[1], percentage)
        if not ad_context is None:
            adversarial_contexts.append((context[0], ad_context))
    return adversarial_contexts

def create_adversarial_dataset(original_file_path, adversarial_file_path, percent_context_to_change=20):
    with open(original_file_path, 'r') as file:
        squad_data = json.load(file)
    
    # crete a hash of context as ID, this will be used to identify the context later
    # context is a tuple of (hash(context), context)
    contexts = [(hash(paragraph['context']), paragraph['context']) for article in squad_data['data'] for paragraph in article['paragraphs']]

    #  Shuffle the contexts
    random.shuffle(contexts)

    # extract the first percent_context_to_change% of contexts to change
    # num_contexts_to_change = len(contexts) * percent_context_to_change // 100
    num_contexts_to_change = 1
    adversarial_contexts = create_adversarial_contexts(contexts[:num_contexts_to_change])
    
    # Replace original contexts with adversarial ones
    # we can use the hash to identify the context
    context_counter = 0

    # The paragraph should be sequential, so the order of following loops 
    # should just be O(n)
    for ad_context in adversarial_contexts:
        for article in squad_data['data']:
            for paragraph in article['paragraphs']:
                if hash(paragraph['context']) == ad_context[0]:
                    paragraph['context'] = ad_context[1]
                    context_counter += 1
                    break
        if context_counter == num_contexts_to_change:
            break
    # for article in squad_data['data']:
    #     for paragraph in article['paragraphs']:
    #         if context_counter < num_contexts_to_change:
    #             paragraph['context'] = adversarial_contexts[context_counter]
    #             context_counter += 1
    
    # Write the modified dataset to a new file
    with open(adversarial_file_path, 'w') as file:
        json.dump(squad_data, file)

# define the main entry point of the script
if __name__ == "__main__":
    # Prompt for a question
    orig_file_path = './Squad/dev-v1.1.json'
    out_file_path = './Squad/dev-v1.1-adversarial.json'
    create_adversarial_dataset(original_file_path=orig_file_path, 
                               adversarial_file_path=out_file_path)
