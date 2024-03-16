import os
import json
from bs4 import BeautifulSoup
from chromedriver_py import binary_path
from selenium import webdriver
from flask import Flask, request, jsonify
import datetime
import re

app = Flask(__name__)

@app.route('/')
def index():
   return "<h1>Hello</h1>"

@app.route('/base', methods=['POST'])
def base():
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

@app.route('/amazon', methods=['GET'])
def amazon():
   try:

      chrome_options = webdriver.ChromeOptions()
      chrome_options.add_argument("--headless")
      chrome_options.add_argument("--remote-debugging-port=9222")
      s = webdriver.ChromeService(executable_path=binary_path)
      driver = webdriver.Chrome(service=s, options=chrome_options)

      # Initialize an empty list to store scraped data
      scraped_data = []
      data = request.get_json()

      if not isinstance(data, list):
         return jsonify({'error': 'Invalid JSON format. Expecting an array of objects.'}), 400

      asins = [item.get('asin') for item in data]
      urls = [item.get('url') for item in data]

      if None in asins or None in urls:
         return jsonify({'error': 'Each object in the array must have "asin" and "url" keys.'}), 400

      if len(asins) != len(urls):
         return jsonify({'error': 'Number of ASINs must match the number of URLs'}), 400
      
      for url in urls:
         driver.get(url)  # Open the URL in the browser
         html_content = driver.page_source  # Get the HTML content

         # Parse the HTML content using Beautiful Soup
         soup = BeautifulSoup(html_content, "html.parser")

         # Extract relevant information from the page (customize this part)
         # title = soup.find("title").text.strip()
         product_title_span = soup.find("span", id="productTitle").text.strip()
         product_price_span = soup.find("span", class_="a-price-whole").text.strip()
         product_seller_span = soup.find("span", class_="offer-display-feature-text-message").text.strip()
         date = datetime.date.today()
         formatted_date = date.strftime("%d-%m-%Y")
         time = datetime.datetime.now().time()
         formatted_time = time.strftime("%I:%M:%S %p")

         # Append the scraped data to the list
         scraped_data.append({"time": formatted_time, "date": formatted_date, "url": url, "prod_title": product_title_span, "price": product_price_span, "seller": product_seller_span})
         with open("scraped_data.json", "w") as json_file:
          json.dump(scraped_data, json_file, indent=3)
      # Save the scraped data to a JSON file
      
         
      driver.quit()  # Close the browser
      scrape_data = [{'asin': asin, 'url': url} for asin, url in zip(asins, urls)]

      with open('amazon.json', 'w') as f:
         json.dump(scrape_data, f, indent=3)

      return jsonify({"message": "Amazon Data Scraped Successfully!"})

   except Exception as e:
      return jsonify({'error': str(e)}), 500

@app.route('/noon', methods=['GET'])
def noon():
    try:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--remote-debugging-port=9222")
        s = webdriver.ChromeService(executable_path=binary_path)
        driver = webdriver.Chrome(service=s, options=chrome_options)

        # Initialize an empty list to store scraped data
        scraped_data = []
        data = request.get_json()

        if not isinstance(data, list):
            return jsonify({'error': 'Invalid JSON format. Expecting an array of objects.'}), 400

        asins = [item.get('asin') for item in data]
        urls = [item.get('url') for item in data]

        if None in asins or None in urls:
            return jsonify({'error': 'Each object in the array must have "asin" and "url" keys.'}), 400

        if len(asins) != len(urls):
            return jsonify({'error': 'Number of ASINs must match the number of URLs'}), 400

        for url in urls:
            driver.get(url)  # Open the URL in the browser
            html_content = driver.page_source  # Get the HTML content

            # Parse the HTML content using Beautiful Soup
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract relevant information from the page (customize this part)
            product_title_span = soup.find("h1", class_="fIMVLF")
            product_price_span = soup.find("div", class_="priceNow")

            if product_price_span:
                product_price_span = product_price_span.text.strip()
                # Define a regex pattern to extract the numeric part of the price
                product_price_pattern = r'\d+\.\d+'
                matches = re.findall(product_price_pattern, product_price_span)
                if matches:
                    product_price = float(matches[0])
                else:
                    product_price = None
            else:
                product_price = None

            product_seller_span = soup.find("span", class_="allOffers")
            date = datetime.date.today()
            formatted_date = date.strftime("%d-%m-%Y")
            time = datetime.datetime.now().time()
            formatted_time = time.strftime("%I:%M:%S %p")

            # Append the scraped data to the list
            scraped_data.append({"time": formatted_time, "date": formatted_date, "url": url, "prod_title": product_title_span, "price": product_price, "seller": product_seller_span})
            with open("scraped_data.json", "w") as json_file:
                json.dump(scraped_data, json_file, indent=3)
        # Save the scraped data to a JSON file

        driver.quit()  # Close the browser
        scrape_data = [{'asin': asin, 'url': url} for asin, url in zip(asins, urls)]

        with open('noon.json', 'w') as f:
            json.dump(scrape_data, f, indent=3)

        return jsonify({"message": "Noon Data Scraped Successfully!"})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/jumia', methods=['POST'])
def jumia():
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

@app.route('/btech', methods=['POST'])
def btech():
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


@app.route('/scrape', methods=['GET'])
def scrape():
   try:

      # chrome_options = Options()
      chrome_options = webdriver.ChromeOptions()
      # chrome_options.binary_location = '/opt/google/chrome/google-chrome'
      chrome_options.add_argument("--headless")
      chrome_options.add_argument("--remote-debugging-port=9222")

      s = webdriver.ChromeService(executable_path=binary_path)
      driver = webdriver.Chrome(service=s, options=chrome_options)
      # driver = webdriver.Chrome(executable_path="./.venv/bin/chromedriver.exe", options=chrome_options)
      # driver = webdriver.Chrome(executable_path="./.venv/bin/chromedriver.exe")

      # Initialize an empty list to store scraped data
      scraped_data = []
      data = request.get_json()

      if not isinstance(data, list):
         return jsonify({'error': 'Invalid JSON format. Expecting an array of objects.'}), 400

      asins = [item.get('asin') for item in data]
      urls = [item.get('url') for item in data]

      if None in asins or None in urls:
         return jsonify({'error': 'Each object in the array must have "asin" and "url" keys.'}), 400

      if len(asins) != len(urls):
         return jsonify({'error': 'Number of ASINs must match the number of URLs'}), 400
      
      for url in urls:
         driver.get(url)  # Open the URL in the browser
         html_content = driver.page_source  # Get the HTML content

         # Parse the HTML content using Beautiful Soup
         soup = BeautifulSoup(html_content, "html.parser")

         # Extract relevant information from the page (customize this part)
         # Example: Get the title
         title = soup.find("title").text.strip()
         product_title_span = soup.find("span", id="productTitle").text.strip()
         product_price_span = soup.find("span", class_="a-price-whole").text.strip()
         product_seller_span = soup.find("span", class_="offer-display-feature-text-message").text.strip()

         # Append the scraped data to the list
         scraped_data.append({"url": url, "title": title, "prod_title": product_title_span, "price": product_price_span, "seller": product_seller_span})



         

      # Save the scraped data to a JSON file
      with open("scraped_data.json", "w") as json_file:
         json.dump(scraped_data, json_file, indent=3)
         
      # return jsonify({"message": "Data scraped successfully!"})
      driver.quit()  # Close the browser
      scrape_data = [{'asin': asin, 'url': url} for asin, url in zip(asins, urls)]

      with open('amazon.json', 'w') as f:
         json.dump(scrape_data, f, indent=3)

      return jsonify({"message": "Data scraped successfully!"})

   except Exception as e:
      return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
   app.run(host='0.0.0.0', port=5000, debug=True)

