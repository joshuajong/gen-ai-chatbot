from openai import OpenAI
import json
import os
# from weaviate.client import WeaviateClient

class ChatBot:
  def __init__(self, knowledge_source, general_context_source):
    # Get the OpenAI API key from environment variables
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
      raise ValueError("OpenAI API key is not set. Please check your .env file.")

    # Load the knowledge source
    with open(knowledge_source, 'r') as f:
      self.knowledge_base = json.load(f)["knowledge_base"]

    # Initialise the open ai client
    self.client = OpenAI(
      api_key=openai_api_key,
    )
    self.openai_api_key = openai_api_key
    # Model should contain some general context in case knowledge base is insufficient to answer the user's query
    with open(general_context_source, 'r') as file:
      self.general_context = file.read()

    # self.weaviate_client = WeaviateClient(openai_api_key)

  def search_knowledge_base_for_best_match(self, user_input):
    for context in self.knowledge_base:
      for question, answer in context["qa_pairs"].items():
        if user_input.lower() in question.lower():
          return answer
  
  # If there is no direct answer we will need to check closest vectors using weaviate
  def search_knowledge_base_for_closest_match(self, user_input):
    client = self.instantiate_weaviate_client()
    response = (
      client.query
      .get("Question", ["question", "answer", "category"])
      .with_near_text({"concepts": [user_input]})
      .with_limit(2)
      .do()
    )
    questions = response.get("data", {}).get("Get", {}).get("Question", [])
    if not questions:
      return None

    output = "Did you mean:\n\n"
    for idx, item in enumerate(questions, start=1):
        question = item.get("question", "Unknown question")
        answer = item.get("answer", "No answer available")
        output += f"{idx}. {question}\n   Answer: {answer}\n\n"
    
    return output

  # Attempts to answer user's query by querying knowledge base, weaviate, and the LLM (in this order)
  def generate_response(self, user_prompt):
    best_match = self.search_knowledge_base_for_best_match(user_prompt)
    if best_match:
      return best_match
    else:
      # closest_match = self.weaviate_client.search_for_closest_match(user_prompt)
      # if closest_match:
      #   return closest_match
      # prompt = self.general_context + "\n\nUser: " + user_prompt + "\n\Customer Support: "
      response = self.client.chat.completions.create(
        messages=[
          {
            "role": "user",
            "content": user_prompt,
            "stop": ["User:", "Customer Support:"],
          }
        ],
        model="gpt-3.5-turbo",
      )
    return response.choices[0].message.content