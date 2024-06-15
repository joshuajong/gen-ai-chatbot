from openai import OpenAI
import json

class ChatBot:
  def __init__(self, knowledge_source, api_key, general_context, weaviate_client):
    # Load the knowledge source
    with open(knowledge_source, 'r') as f:
      self.knowledge_base = json.load(f)["knowledge_base"]

    # Initialise the open ai client
    self.client = OpenAI(
      api_key=api_key,
    )
    # Model should contain some general context in case knowledge base is insufficient to answer the user's query
    self.general_context = general_context

    # Initialise weaviate client for vector search
    self.weaviate_client = weaviate_client

  def search_knowledge_base_for_best_match(self, user_input):
    for context in self.knowledge_base:
      for question, answer in context["qa_pairs"].items():
        if user_input.lower() in question.lower():
          return answer
    return None 
  
  def search_weaviate_for_best_match(self, user_input):
    query = {
            "concepts": [user_input],
            "certainty": 0.7
    }
    response = self.weaviate_client.query.get("Document", ["content"]).with_near_text(query).do()
    
    if response['data']['Get']['Document']:
      return response['data']['Get']['Document'][0]['content']
    return "No additional information found."
  
  def generate_response(self, user_prompt):
    search_knowledge_base_for_best_match = self.search_knowledge_base_for_best_match(user_prompt)
    if search_knowledge_base_for_best_match:
      return search_knowledge_base_for_best_match
    else:
      prompt = self.general_context + "\n\nUser: " + user_prompt + "\n\Customer Support: "
      response = self.client.chat.completions.create(
        messages=[
          {
            "role": "user",
            "content": prompt,
            "stop": ["User:", "Customer Support:"],
          }
        ],
        model="gpt-3.5-turbo",
      )
    return response.choices[0].message.content