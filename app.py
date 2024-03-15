import os
from flask import Flask, request, render_template, jsonify, Response, send_from_directory

app = Flask(__name__)


@app.route('/')
def index():
   return "<h1>Hello</h1>"

@app.route('/amazon', methods=['GET', 'POST'])
def amazon():
   platform = request.json['platform']
   sku = request.json['sku']

   with open('amazon.json', 'w') as f:
      f.write(f'{platform}, {sku}')

   return jsonify({'message': 'Data Received!'})


if __name__ == '__main__':
   app.run(host='0.0.0.0', port=5000, debug=True)