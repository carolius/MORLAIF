from openai import OpenAI
import os
import random
import json
from tqdm import tqdm
import time
import argparse
client = OpenAI()

parser = argparse.ArgumentParser()
parser.add_argument("--multi-objective", type=bool, default=True)
parser.add_argument("--principle_folder", type=str, default=None)
parser.add_argument("--principle_name", type=str, default=None)
parser.add_argument("--feedback_model", type=str, default="gpt-3.5-turbo-0125")
parser.add_argument("--CoT", type=bool, default=False)
parser.add_argument("--few_shot_path", type=str, default=None)
parser.add_argument("--principle_path", type=str, default=None)
parser.add_argument("--dataset_path", type=str, default=None)
parser.add_argument("--save_path", type=str, default=None)
config = parser.parse_args()

def get_few_shot_examples(few_shot_path,principles,chain_of_thought=False):
    messages = []
    for example in open(few_shot_path, 'r'):
        example = json.loads(example.strip())
        principle = random.choice(principles)
        prompt = example["prompt"]
        options = example["options"]
        choice = example["choice"]
        CoT = example["CoT"]
        ending = "Please respond only with A or B. The answer is:\n\n"
        if chain_of_thought:
            conversation = prompt + principle + options
            choice = CoT + choice
        else:
            conversation = prompt + principle + options + ending
        messages.append({"role": "user", "content": conversation})
        messages.append({"role": "assistant", "content": choice})
    return messages

def get_principles(principle_path):
    principles = []
    for principle in open(principle_path, 'r'):
        principle = json.loads(principle.strip())
        principle = principle["principle"]
        principles.append(principle)
    return principles
def get_principles_from_folder(principle_folder_path):
    with open(os.path.join(principle_folder_path, config.principle_name + '.txt'), 'r') as infile:
        principles = infile.readlines()
    return principles
        
def prepare_request(model,conversation, responseA, responseB, principle,messages=[]):
    """
    Asks the feedback model which response is better based on a given principle using logits.
    
    Args:
    - model (str): The model to use for feedback.
    - conversation (str): The conversation between the user and assistant which is to be rated.
    - responseA (str): The first response.
    - responseB (str): The second response.
    - principle (str): The principle to judge the responses.
    - messages (list): A list of messages to be prepended, used for few-shot examples.
    
    Returns:
    - logits_for_A the logits for response A
    - logits_for_B the logits for response B
    """


    prompt = f"Consider the following conversation between a human and an assistant: \n"\
            f"Conversation: {conversation} \n '{principle}', "\
            "Options: \n" \
            f"A. {responseA}\n" \
            f"B. {responseB}\n" \
            f"Please respond only with A or B. The answer is:\n\n"
    messages.append({"role": "user", "content": prompt})  
    
    request = {
        "model": model,
        "messages": messages,
        "max_tokens": 1,
        "logprobs": True,
        "top_logprobs": 5
    }
    return request


    #print(response)
    # Extracting the logits for the last tokens (which should correspond to "A" or "B")
    # logprobs = {}
    # for logprob in response.choices[0].logprobs.content[0].top_logprobs:
    #     logprobs[logprob.token]= logprob.logprob
    # logits_for_A = logprobs.get('A', -10)
    # logits_for_B = logprobs.get('B', -10)

    # return logits_for_A,logits_for_B


def process_dataset(input_filename, output_filename, model):
    if config.multi_objective:
        principles = get_principles_from_folder(config.principle_folder)
    else: 
        principles = get_principles(config.principle_path)
    if config.few_shot_path is not None:
        conversation = get_few_shot_examples(config.few_shot_path,principles)
    else:
        conversation = []
    with open(input_filename, 'r', encoding='utf-8') as infile, open(output_filename, 'w', encoding='utf-8') as outfile:
        lines = infile.readlines()
        for line in tqdm(lines):
            input_dict = json.loads(line.strip())
            question = input_dict["prompt"]
            responseA = input_dict["responseA"]
            responseB = input_dict["responseB"]
            principle = random.choice(principles)
            request = prepare_request(model,question, responseA, responseB, principle,messages=conversation.copy())
            #result_dict = {
            #    "prompt": question,
            #    "responseA": responseA,
            #    "responseB": responseB
            #}
            #result_dict["logits_A"] = logits_for_A
            #result_dict["logits_B"] = logits_for_B
            
            result_json_str = json.dumps(request)
            outfile.write(f"{result_json_str}\n")
     
process_dataset(config.dataset_path,config.save_path,config.feedback_model)






