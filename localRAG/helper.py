import chromadb  # we used nomic-embed-text model for embeddings 
import ollama
from db_methods import store_conversations
import ast
import tqdm 

client= chromadb.Client()


system_prompt= {
    'You are an AI assistant that has memory of every conversation you have ever had with this user.'
    'On every prompt from the user, the system has checked for any relevant messages, you have had with the users.'
    'If any embedded previous conversations are attached, use them for context to responding to the user.'
    'If the context is relevant and useful to responding. If the recalled conversation are irrelavant, disregard speaking about them and respond normally as an AI assistant.'
    'Do not talk about recalling conversations, just use any useful data from the previous data from the previous conversations and respond normally as an intelligent ai assistant.'
}
convo = []

# Main
def stream_response(prompt):
    #convo.append({'role':'user', 'content':prompt})
    response= " "
    stream = ollama.chat(model='llama3', messages=convo, stream=True) 
    print('\nAssistant')

    for chunk in stream:
        content = chunk['message']['content']
        response += content 
        print(content, end='', flush=True) 

    print('\n') 
    store_conversations(prompt=prompt, response=response) 
    convo.append({'role':'assistant', 'content':response})


def create_vector_db(conversations):
    vector_db_name = "conversations" 

    try:
        client.delete_collection(name=vector_db_name) 
    except ValueError:
        pass

    vector_db = client.create_collection(name=vector_db_name)

    for c in conversations:
        serialized_convo = f"prompt: {c['prompt']} response: {c['response']}"
        response = ollama.embeddings(model='nomic-embed-text', prompt=serialized_convo) 
        embedding = response['embedding']

        vector_db.add(
            ids=[str(c['id'])],
            embeddings = [embedding],
            documents = [serialized_convo] 
        )

def retrieve_embeddings(queries, results_per_query=2):
    embeddings = []
    for query in tqdm(queries, desc="Processing queries to vector database"):
        response = ollama.embeddings(model='nomic-embed-text',prompt=query)
        query_embeddings = response['embedding']

        vector_db = client.get_collection(name='conversations') 
        results = vector_db.query(query_embeddings=[query_embeddings], n_results = results_per_query)    
        best_embeddings = results['documents'][0]

        for best in best_embeddings:
            if best not in embeddings:
                if "yes" in classify_embeddings(query=query, context=best) :
                    embeddings.append(best) 

    return embeddings    

    # response = ollama.embeddings(model='nomic-embed-text',prompt=prompt) 
    # prompt_embedding = response['embedding'] 
    
    # vector_db = client.get_collection(name='conversations') 
    # results = vector_db.query(query_embeddings=[prompt_embedding], n_results = 1) 
    # best_embedding = results['documents'][0][0] 

    #return best_embedding

def create_queries(prompt):
    query_msg = (
        'You are an AI assistant that has memory of every conversation you have ever had with this user.'
    'On every prompt from the user, the system has checked for any relevant messages, you have had with the users.'
    'If any embedded previous conversations are attached, use them for context to responding to the user.'
    'If the context is relevant and useful to responding. If the recalled conversation are irrelavant, disregard speaking about them and respond normally as an AI assistant.'
    'Do not talk about recalling conversations, just use any useful data from the previous data from the previous conversations and respond normally as an intelligent ai assistant.'
    )

    # implementing multi-shot learning for better output formats
    query_convo = [
        {'role':'system', 'content': query_msg},
        {'role':'user', 'content':'write an email to my car insurance and create a pursuasive request for them to lower my montly rate.'},
        
        {'role':'assistant', 'content':"what is the users name? : what is the users current auto insurance provider? : what is the montly rate the user currently pays for the auto insurance?"},
        {'role':'user', 'content':prompt}
    ]

    response = ollama.chat(model='llama3', messages=query_convo) 
    print(f"\nVector database queries: {response['message']['content']}\n")

    try:
        return ast.literal_eval(response['message']['content'])
    except:
        return [prompt] 
    

def classify_embeddings(query, context):
    classify_msg = (
        'You are an embedding classification AI agent. Your input will be a prompt and one embedded chunk of text.'
        'You will not respond as an AI assistant. You only respond "yes" or "no"'
        'Determine whether the context contains data that directly is related to the search query.'
        'If the context is seemingly exactly what the search query needs, respond "yes" if it is anything but directly related respond "no"'
        'Do not respond "yes" unless the content is highly relevant to the search query'
    )
    classify_convo = [
        {'role':'system', 'content':classify_msg},
        {'role':'user', 'content':f'SEARCH QUERY: What is the user name?\n\n EMBEDDED CONTEXT: You are Jagan, What can i help you with today?'},
        {'role':'assistant', 'content':'yes'},
        {'role':'user','content':f'SEARCH QUERY: llama3 Python voice assistant \n\n EMBEDDED CONTEXT: Siri is a voice assistant on Apple ios and Mac os.'},
        {'role':'assistant','content':'no'},
        {'role':'user', 'content':f'SEARCH QUERY: {query} \n\n EMBEDDED CONTEXT: {context}'},
    ]

    response = ollama.chat(model='llama3', messages=classify_convo) 

    return response['message']['content'].strip().lower()   

def recall(prompt):
    queries = create_queries(prompt=prompt)
    embeddings = retrieve_embeddings(queries=queries) 

    convo.append({'role':'user', 'content': f'MEMORIES:{embeddings} \n\n PROMPT:{prompt}'})
    
    print(f"\n{len(embeddings)} message : response embeddings added for context")