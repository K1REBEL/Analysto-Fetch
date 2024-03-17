import os
import json
import datetime
import re
from bs4 import BeautifulSoup
from chromedriver_py import binary_path
from selenium import webdriver
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests

app = Flask(__name__)

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--remote-debugging-port=9222")
s = webdriver.ChromeService(executable_path=binary_path)


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

      # chrome_options = webdriver.ChromeOptions()
      # chrome_options.add_argument("--headless")
      # chrome_options.add_argument("--remote-debugging-port=9222")
      # s = webdriver.ChromeService(executable_path=binary_path)
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
   #  try:
   #      chrome_options = webdriver.ChromeOptions()
   #      chrome_options.add_argument("--headless")
   #      chrome_options.add_argument("--remote-debugging-port=9222")
   #      s = webdriver.ChromeService(executable_path=binary_path)
   #      driver = webdriver.Chrome(service=s, options=chrome_options)

   #      # Initialize an empty list to store scraped data
   #      scraped_data = []
   #      data = request.get_json()

   #      if not isinstance(data, list):
   #          return jsonify({'error': 'Invalid JSON format. Expecting an array of objects.'}), 400

   #      asins = [item.get('asin') for item in data]
   #      urls = [item.get('url') for item in data]

   #      if None in asins or None in urls:
   #          return jsonify({'error': 'Each object in the array must have "asin" and "url" keys.'}), 400

   #      if len(asins) != len(urls):
   #          return jsonify({'error': 'Number of ASINs must match the number of URLs'}), 400

   #      for url in urls:
   #          driver.get(url)  # Open the URL in the browser

   #          html_content = driver.page_source  # Get the HTML content

   #          # Parse the HTML content using Beautiful Soup
   #          soup = BeautifulSoup(html_content, "html.parser")

   #          # Extract relevant information from the page (customize this part)
   #          title = soup.find("title")
   #          print(title)
   #          product_title_span = soup.find("h1", class_="fIMVLF")
   #          product_price_span = soup.find("div", class_="priceNow")

   #          if product_price_span:
   #              product_price_span = product_price_span.text.strip()
   #              # Define a regex pattern to extract the numeric part of the price
   #              product_price_pattern = r'\d+\.\d+'
   #              matches = re.findall(product_price_pattern, product_price_span)
   #              if matches:
   #                  product_price = float(matches[0])
   #              else:
   #                  product_price = None
   #          else:
   #              product_price = None

   #          product_seller_span = soup.find("span", class_="allOffers")
   #          date = datetime.date.today()
   #          formatted_date = date.strftime("%d-%m-%Y")
   #          time = datetime.datetime.now().time()
   #          formatted_time = time.strftime("%I:%M:%S %p")

   #          # Append the scraped data to the list
   #          scraped_data.append({"time": formatted_time, "date": formatted_date, "title": title, "url": url, "product_title": product_title_span, "price": product_price, "seller": product_seller_span})
   #          with open("scraped_data.json", "w") as json_file:
   #              json.dump(scraped_data, json_file, indent=3)
   #      # Save the scraped data to a JSON file

   #      driver.quit()  # Close the browser
   #      scrape_data = [{'asin': asin, 'url': url} for asin, url in zip(asins, urls)]

   #      with open('noon.json', 'w') as f:
   #          json.dump(scrape_data, f, indent=3)

   #      return jsonify({"message": "Noon Data Scraped Successfully!"})

   #  except Exception as e:
   #      return jsonify({'error': str(e)}), 500
   try:

      # chrome_options = webdriver.ChromeOptions()
      # chrome_options.add_argument("--headless")
      # chrome_options.add_argument("--remote-debugging-port=9222")
      # s = webdriver.ChromeService(executable_path=binary_path)
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
         title = soup.find("title")
         product_title_span = soup.find("h1", class_="fIMVLF")
         product_price_span = soup.find("span", class_="priceNow")
         product_seller_span = soup.find("span", class_="allOffers")
         date = datetime.date.today()
         formatted_date = date.strftime("%d-%m-%Y")
         time = datetime.datetime.now().time()
         formatted_time = time.strftime("%I:%M:%S %p")

         # Append the scraped data to the list
         scraped_data.append({"time": formatted_time, "date": formatted_date, "url": url, "title":title, "prod_title": product_title_span, "price": product_price_span, "seller": product_seller_span})
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

# @app.route('/jumia', methods=['GET'])
# def jumia():
#     try:
#         scraped_data = []  # Initialize an empty dictionary to store scraped data
#         data = request.get_json()

#         if not isinstance(data, list):
#             return jsonify({'error': 'Invalid JSON format. Expecting an array of objects.'}), 400

#         for item in data:
#             query = item.get('query')
#             url = f"https://www.jumia.com.eg/catalog/?q={query}"
#             response = requests.get(url)
#             soup = BeautifulSoup(response.content, "html.parser")

#             # Extract all products from the page
#             products = soup.select("article.prd")
#             query_data = []  # Initialize an empty list to store data for this query
#             final_data = []
#             scraped_data = []

#             for product in products:
#                 price = product.find("div", class_="prc")
#                 prod_url = product.select(("article.prd > a"))
#                 href = prod_url[1]["href"]
#                 href_data = "https://www.jumia.com.eg"+href
#                 if price:
#                     product_price_class = price.text.strip()
#                     product_price_class = product_price_class.replace(",", "")
#                     product_price_pattern = r'\d+\.\d+'
#                     matches = re.findall(product_price_pattern, product_price_class)
#                     if matches:
#                         product_price = float(matches[0])
#                     else:
#                         product_price = None

#                     # Append the scraped data for this product to the query data list
#                     query_data.append({"price": product_price, "url": href_data})

#             # Add the query data to the scraped_data dictionary
#             # scraped_data[query] = query_data
#               # Find the lowest price for this query
#             lowest_price = None
#             lowest_price_url = None
#             if query_data:
#                 lowest_price_data = min(query_data, key=lambda x: x["price"])
#                 lowest_price = lowest_price_data["price"]
#                 lowest_price_url = lowest_price_data["url"]

#             # Add the lowest price for this query to the scraped_data dictionary`
#             final_data.append({"price": lowest_price, "url": lowest_price_url})
#             # scraped_data[query] = final_data  

#             response2 = requests.get(lowest_price_url)
#             soup1 = BeautifulSoup(response2.content, "html.parser")

               
#             product_title_span = soup1.select("div.-prl > h1.-pts")[0].text
#             product_price_span = soup1.find("span", class_="-fs24").text.strip()
#             product_seller_span = soup1.select("div.-pts > section.card > div.-pas > p.-pbs")[0].text
#             date = datetime.date.today()
#             formatted_date = date.strftime("%d-%m-%Y")
#             time = datetime.datetime.now().time()
#             formatted_time = time.strftime("%I:%M:%S %p")

#          # Append the scraped data to the list
#             scraped_data.append({"query": query, "time": formatted_time, "date": formatted_date, "url": url, "prod_title":product_title_span, "price":product_price_span, "seller":product_seller_span}) 

#         with open("scraped_data.json", "w") as json_file:
#             json.dump(scraped_data, json_file, indent=3)

#         return jsonify({"message": "Jumia Data Scraped Successfully!"})

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
   
@app.route('/jumia', methods=['GET'])
def jumia():
    try:
        scraped_data = []  # Initialize an empty list to store scraped data
        data = request.get_json()

        if not isinstance(data, list):
            return jsonify({'error': 'Invalid JSON format. Expecting an array of objects.'}), 400

        for item in data:
            query = item.get('query')
            url = f"https://www.jumia.com.eg/catalog/?q={query}"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")

            # Extract all products from the page
            products = soup.select("article.prd")
            query_data = []  # Initialize an empty list to store data for this query

            for product in products:
                price = product.find("div", class_="prc")
                prod_url = product.select(("article.prd > a"))
                href = prod_url[1]["href"]
                href_data = "https://www.jumia.com.eg"+href
                if price:
                    product_price_class = price.text.strip()
                    product_price_class = product_price_class.replace(",", "")
                    product_price_pattern = r'\d+\.\d+'
                    matches = re.findall(product_price_pattern, product_price_class)
                    if matches:
                        product_price = float(matches[0])
                    else:
                        product_price = None

                    # Append the scraped data for this product to the query data list
                    query_data.append({"price": product_price, "url": href_data})

            # Find the lowest price for this query
            lowest_price = None
            lowest_price_url = None
            if query_data:
                lowest_price_data = min(query_data, key=lambda x: x["price"])
                lowest_price = lowest_price_data["price"]
                lowest_price_url = lowest_price_data["url"]

            # Scrap additional data from the lowest price URL
            response2 = requests.get(lowest_price_url)
            soup1 = BeautifulSoup(response2.content, "html.parser")
            product_title_span = soup1.select("div.-prl > h1.-pts")[0].text
            product_price_span = soup1.find("span", class_="-fs24").text.strip()
            product_seller_span = soup1.select("div.-pts > section.card > div.-pas > p.-pbs")[0].text
            date = datetime.date.today()
            formatted_date = date.strftime("%d-%m-%Y")
            time = datetime.datetime.now().time()
            formatted_time = time.strftime("%I:%M:%S %p")

            # Append the scraped data to the list
            scraped_data.append({
                "query": query,
                "time": formatted_time,
                "date": formatted_date,
                "product_url":lowest_price_url,
                "url": url,
                "prod_title": product_title_span,
                "price": product_price_span,
                "seller": product_seller_span
            }) 

        with open("scraped_data.json", "w") as json_file:
            json.dump(scraped_data, json_file, indent=3)

        return jsonify({"message": "Jumia Data Scraped Successfully!"})

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

      # chrome_options = webdriver.ChromeOptions()
      # chrome_options.add_argument("--headless")
      # chrome_options.add_argument("--remote-debugging-port=9222")
      # s = webdriver.ChromeService(executable_path=binary_path)
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
      
      def scrape_url(url):
            # r = requests.get(url)
            driver.get(url)  # Open the URL in the browser
            html_content = driver.page_source  # Get the HTML content

            soup = BeautifulSoup(html_content, "html.parser")
            product_title_span = soup.find("span", id="productTitle").text.strip()
            product_price_span = soup.find("span", class_="a-price-whole").text.strip()
            product_seller_span = soup.find("span", class_="offer-display-feature-text-message").text.strip()
            date = datetime.date.today()
            formatted_date = date.strftime("%d-%m-%Y")
            time = datetime.datetime.now().time()
            formatted_time = time.strftime("%I:%M:%S %p")
            return {"date": formatted_date, "time": formatted_time, "url": url, "prod_title": product_title_span, "price": product_price_span, "seller": product_seller_span}

        # Use ThreadPoolExecutor to run scrape_url concurrently
      with ThreadPoolExecutor(max_workers=10) as executor:
         futures = [executor.submit(scrape_url, url) for url in urls]

      results = [future.result() for future in futures]

      with open("scraped_data.json", "w") as json_file:
         json.dump(results, json_file, indent=3)
      
         
      driver.quit()  # Close the browser
      # scrape_data = [{'asin': asin, 'url': url} for asin, url in zip(asins, urls)]

      # with open('amazon.json', 'w') as f:
      #    json.dump(scrape_data, f, indent=3)

      return jsonify({"message": "Amazon Data Scraped Successfully!"})

   except Exception as e:
      return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
   app.run(host='0.0.0.0', port=5000, debug=True)

# if product_price_span:
   #              product_price_span = product_price_span.text.strip()
   #              # Define a regex pattern to extract the numeric part of the price
   #              product_price_pattern = r'\d+\.\d+'
   #              matches = re.findall(product_price_pattern, product_price_span)
   #              if matches:
   #                  product_price = float(matches[0])
   #              else:
   #                  product_price = None
   #          else:
   #              product_price = None