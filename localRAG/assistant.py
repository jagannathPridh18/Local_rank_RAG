# AI agent that stores and logically retreives any message.  
# additional features to be implemented : 
# 1. Multimodality (images & text)  
# 2. using tools integration for scraping 
# 3. 

from helper import create_vector_db, stream_response, recall, convo
from db_methods import fetch_conversations, remove_last_conversation, store_conversations

conversations = fetch_conversations()
create_vector_db(conversations=conversations)

while True:
    prompt = input('user: \n')
    # context = retrieve_embeddings(prompt=prompt) 
    # prompt = f'USER PROMPT: {prompt} \nCONTEXT FROM EMBEDDINGS: {context}'
    if prompt[:7].lower() == '/recall':
        prompt = prompt[8:] 
        stream_response(prompt=prompt) 
    elif prompt[:7].lower()  == '/forget':
        remove_last_conversation()
        convo = convo[:-2]
        print('\n')
    elif prompt[:9].lower() == '/memorize':
        prompt = prompt[10:]
        store_conversations(prompt=prompt, response="Memory stored.")
        print('\n')
    else : 
        convo.append({'role':'user', 'content':prompt})
        stream_response(prompt=prompt) 
    
    stream_response(prompt=prompt) 
