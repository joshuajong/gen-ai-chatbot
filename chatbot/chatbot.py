from openai import OpenAI
import json
import weaviate
import os
import weaviate.classes as wvc
import weaviate.classes.config as wvcc

class ChatBot:
  def __init__(self, knowledge_source, general_context):
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
    self.general_context = general_context

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
  
  # Instantiates a client to communicate with the vector database
  def instantiate_weaviate_client(self, version="v3"):
    # Get the Weaviate API key from environment variables
    weaviate_api_key = os.environ.get("WEAVIATE_API_KEY")
    cluster_url = os.getenv("WEAVIATE_CLUSTER_URL")
    if not weaviate_api_key or not cluster_url:
      raise ValueError("Weaviate API key or cluster URL key is not set. Please check your .env file.")
    else:
      if version == "v3":
        weaviate_client = weaviate.Client(
          url = cluster_url,  # Replace with your Weaviate endpoint
          auth_client_secret=weaviate.auth.AuthApiKey(weaviate_api_key),  # Replace with your Weaviate instance API key
          additional_headers = {
              "X-OpenAI-Api-Key": self.openai_api_key  # Replace with your inference API key
          }
        )
      else:
        weaviate_client = weaviate.connect_to_weaviate_cloud(
          cluster_url=cluster_url,
          auth_credentials=weaviate.auth.AuthApiKey(weaviate_api_key),
          headers={
            "X-OpenAI-Api-Key": self.openai_api_key # Replace with your inference API key
          }
        )
      return weaviate_client

  # Initial setup for weaviate when the collection isnt found
  def setup_weaviate_collection(self):
    client = self.instantiate_weaviate_client("v4")
    collection = client.collections.get("Question")
    if collection is not None:
      print("Collection has been created and populated")
      client.close()
      return
      
    try:
      class_obj = {
        "class": "Question",
        "vectorizer": "text2vec-openai",
        "moduleConfig": {
            "text2vec-openai": {},
            "generative-openai": {}
        }
      }
      client.schema.create_class(class_obj)

      with open(self.knowledge_source, 'r') as f:
        knowledge_base = json.load(f)["knowledge_base"]

        client.batch.configure(batch_size=100)  # Configure batch
        with client.batch as batch:  # Initialize a batch process
          for context in knowledge_base:
            for question, answer in context["qa_pairs"].items():
              properties = {
                "answer": answer,
                "question": question,
                "category": context['context'],
              }
            batch.add_data_object(
                data_object=properties,
                class_name="Question"
            )
    finally:
      pass
        # client.close()

  # Attempts to answer user's query by querying knowledge base, weaviate, and the LLM (in this order)
  def generate_response(self, user_prompt):
    best_match = self.search_knowledge_base_for_best_match(user_prompt)
    if best_match:
      return best_match
    else:
      closest_match = self.search_knowledge_base_for_closest_match(user_prompt)
      if closest_match:
        return closest_match
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