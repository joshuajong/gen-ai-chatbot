from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import os
from chatbot.chatbot import ChatBot
import json

# Weaviate imports
# import weaviate
# import weaviate.classes as wvc
# import weaviate.classes.config as wvcc
# from weaviate.classes.query import MetadataQuery

# Load environment variables from .env file
load_dotenv()

knowledge_source = './knowledgebase/sample_data.json'
general_context_source = './knowledgebase/general_context.txt'

chatbot = ChatBot(knowledge_source, general_context_source)

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
  app.run(debug=True, port=5001)
