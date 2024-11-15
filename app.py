from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import os
from chatbot.chatbot import ChatBot
import json
import sys

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
CORS(app)

@app.after_request
def add_cors_headers(response):
  response.headers['Access-Control-Allow-Origin'] = '*'
  response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
  response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
  return response

@app.route('/api/ask', methods=['POST'])
def support():
  user_message = request.json.get('message')
  if not user_message:
    return jsonify({'error': 'Message cannot be empty'}), 400
  
  response = chatbot.generate_response(user_message)
  return jsonify({'reply': response})

if __name__ == "__main__":
    from os import environ
    app.run(host="0.0.0.0", port=int(environ.get("PORT", 5001)))