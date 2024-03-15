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

      if not isinstance(data, list):
         return jsonify({'error': 'Invalid JSON format. Expecting an array of objects.'}), 400

      platforms = [item.get('platform') for item in data]
      skus = [item.get('sku') for item in data]

      if None in platforms or None in skus:
         return jsonify({'error': 'Each object in the array must have "platform" and "sku" keys.'}), 400

      if len(platforms) != len(skus):
         return jsonify({'error': 'Number of platforms must match number of skus'}), 400

      amazon_data = [{'platform': platform, 'sku': sku} for platform, sku in zip(platforms, skus)]

      with open('amazon.json', 'w') as f:
         json.dump(amazon_data, f)

      return jsonify({'message': 'Data Received!'})

   except Exception as e:
      return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=5000, debug=True)

