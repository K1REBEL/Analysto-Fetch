import os
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
   return "<h1>Hello</h1>"

@app.route('/amazon', methods=['POST'])
def amazon():
   try:
      data = request.get_json()
      platform = data.get('platform')
      sku = data.get('sku')

      if platform is None or sku is None:
         return jsonify({'error': 'Missing platform or sku in request'}), 400

      with open('amazon.json', 'w') as f:
         json.dump(data, f)

      return jsonify({'message': 'Data Received!'})

   except Exception as e:
      return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=5000, debug=True)
