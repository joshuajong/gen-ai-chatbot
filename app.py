from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import os
from chatbot.chatbot import ChatBot
import weaviate
import weaviate.classes as wvc
import weaviate.classes.config as wvcc
import json
from weaviate.classes.query import MetadataQuery

# Load environment variables from .env file
load_dotenv()

# Get the OpenAI API key from environment variables
openai_api_key = os.environ.get("OPENAI_API_KEY")
if not openai_api_key:
  raise ValueError("OpenAI API key is not set. Please check your .env file.")


knowledge_source = './knowledgebase/sample_data.json'
general_context = "We are a customer support service for an online retail store. We handle inquiries related to our return policy, shipping information, product details, and other customer service issues. If the question asked is unrelated, say you do not know. Do not attempt to answer the question."

# Initial setup for weaviate
def instantiate_weaviate_client(version="v3"):
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
            "X-OpenAI-Api-Key": openai_api_key  # Replace with your inference API key
        }
      )
    else:
      weaviate_client = weaviate.connect_to_weaviate_cloud(
        cluster_url=cluster_url,
        auth_credentials=weaviate.auth.AuthApiKey(weaviate_api_key),
        headers={
          "X-OpenAI-Api-Key": openai_api_key # Replace with your inference API key
        }
      )
    return weaviate_client

def setup_weaviate_collection():
  client = instantiate_weaviate_client("v4")
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

    with open(knowledge_source, 'r') as f:
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

def query_weaviate_collection(query):
  client = instantiate_weaviate_client()
  try:
    response = (
      client.query
      .get("Question", ["question", "answer", "category"])
      .with_near_text({"concepts": [query]})
      .with_limit(2)
      .do()
    )

    print(json.dumps(response, indent=4))
    
  finally:
    pass
      # weaviate_client.close()  # Close client gracefully

def main():
  # setup_weaviate_collection()
  query_weaviate_collection("where order")

# chatbot = ChatBot(knowledge_source, openai_api_key, general_context, weaviate_client)

app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route('/')
def home():
  return render_template('index.html')

@app.route('/support', methods=['POST'])
def support():
  user_message = request.json.get('message')
  response = chatbot.generate_response(user_message)
  return jsonify({'response': response})

if __name__ == '__main__':
  # app.run(debug=True, port=5001)
  main()
