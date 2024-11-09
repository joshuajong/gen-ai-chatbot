import os
import weaviate
import json

import weaviate.classes as wvc
import weaviate.classes.config as wvcc

class WeaviateClient:
  def __init__(self, openai_api_key, version="v3"):
    self.openai_api_key = openai_api_key
    self.version = version
    self.client = self.instantiate_weaviate_client()

  def instantiate_weaviate_client(self):
    weaviate_api_key = os.environ.get("WEAVIATE_API_KEY")
    cluster_url = os.getenv("WEAVIATE_CLUSTER_URL")
    if not weaviate_api_key or not cluster_url:
      raise ValueError("Weaviate API key or cluster URL key is not set. Please check your .env file.")
    
    if self.version == "v3":
      return weaviate.Client(
        url=cluster_url,
        auth_client_secret=weaviate.auth.AuthApiKey(weaviate_api_key),
        additional_headers={"X-OpenAI-Api-Key": self.openai_api_key}
      )
    else:
      return weaviate.connect_to_wcs(
        cluster_url=cluster_url,
        auth_credentials=weaviate.auth.AuthApiKey(weaviate_api_key),
        headers={"X-OpenAI-Api-Key": self.openai_api_key}
      )

  def search_for_closest_match(self, user_input):
    response = (
      self.client.query
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

  def setup_collection(self, knowledge_source):
    collection = self.client.collections.get("Question")
    if collection is not None:
      print("Collection has been created and populated")
      self.client.close()
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
      self.client.schema.create_class(class_obj)

      with open(knowledge_source, 'r') as f:
        knowledge_base = json.load(f)["knowledge_base"]

        self.client.batch.configure(batch_size=100)
        with self.client.batch as batch:
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
      # self.client.close()