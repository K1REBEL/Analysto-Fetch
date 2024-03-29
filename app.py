import os
import re
import json
import time
import queue
import redis
import random
import requests
import datetime
# import schedule
import threading
import subprocess
import concurrent.futures
from scrapingant_client import ScrapingAntClient, ScrapingantClientException
# from check_proxies import prepare
# import check_proxies
from celery import Celery
from bs4 import BeautifulSoup
from selenium import webdriver
from chromedriver_py import binary_path
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

# Configure Celery
# 'redis://localhost:6379/0'

# app.config['CELERY_BROKER_URL'] = 'redis-13354.c11.us-east-1-2.ec2.cloud.redislabs.com:13354'  # Update with your Redis server URL
# app.config['CELERY_RESULT_BACKEND'] = 'redis-13354.c11.us-east-1-2.ec2.cloud.redislabs.com:13354'  # Update with your Redis server URL
# celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
# celery.conf.update(app.config)

chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument("--headless")
chrome_options.add_argument("--remote-debugging-port=9222")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36")  # Set user-agent header
s = webdriver.ChromeService(executable_path=binary_path)
q = queue.Queue()


def split_array(arr):
      # Calculate the size of each subarray
   subarray_size = len(arr) // 10
      # Split the array into 5 subarrays
   subarrays = [arr[i * subarray_size: (i + 1) * subarray_size] for i in range(10)]

   return subarrays


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
   scraped_data = []
   data = request.get_json()
   if not isinstance(data, list):
      return jsonify({'error': 'Invalid JSON format. Expecting an array of objects.'}), 400

   asins = [item.get('asin') for item in data]
   urls = [item.get('url') for item in data]

   if None in asins or None in urls:
      return jsonify({'error': 'Each object in the array must have "asin" and "url" keys.'}), 400

   if len(urls) > 100:
      return jsonify({'error': 'Too Many Products, Max is 100.'}), 400

   if len(asins) != len(urls):
      return jsonify({'error': 'Number of ASINs must match the number of URLs'}), 400
   
   def scrape(url, retry_count = 0):
         max_retries = 5
         scrappers = get_scrappers()
         scrapper = random.choice(scrappers)
         original_index = scrappers.index(scrapper)

         if scrapper["credits"] >= scrapper["deductible"]:
            if scrapper["service"] == "scrapingant":
               agent = "scrapingAnt"
               print(scrapper)
               try:
                  client = ScrapingAntClient(token=f"{scrapper['api_key']}")
                  result = client.general_request(
                     url,
                     browser=True,
                     return_page_source=True
                     # ,block_resource='image'
                  )
                  scrapper["credits"] -= scrapper["deductible"]
                  scrappers[original_index] = scrapper
                  html_content = result.content
               except Exception as e:
                  print(f'Got exception while parsing data {repr(e)}')
                  return scrape(url, retry_count + 1)

            elif scrapper["service"] == "scrapingdog":
               print(scrapper)
               agent = "scrapingdog"
               params = {
                  "api_key": f"{scrapper['api_key']}",
                  "url": url,
                  "dynamic": "true",
               }
               try:

                  response = requests.get(f"{scrapper['service_url']}", params=params)
                  scrapper["credits"] -= scrapper["deductible"]
                  scrappers[original_index] = scrapper

                  html_content = response.text
               except Exception as e:
                  print(f'Got exception while parsing data {repr(e)}')
                  return scrape(url, retry_count + 1)
               # return(response.text)
            with open("scrappers.json", "w") as json_file:
               json.dump(scrappers, json_file, indent=3)

            try:
               soup = BeautifulSoup(html_content, "html.parser")

               date = datetime.date.today()
               formatted_date = date.strftime("%d-%m-%Y")
               time = datetime.datetime.now().time()
               formatted_time = time.strftime("%I:%M:%S %p")

               product_title_span = soup.find("span", id="productTitle").text.strip()
               product_price_span = soup.find("span", id="tp_price_block_total_price_ww").text.strip()
               product_seller_span = soup.find("a", id="sellerProfileTriggerId")
               if(product_seller_span):
                  seller = product_seller_span.text.strip()
               else:
                  seller = soup.select_one("div.offer-display-feature-text > span.offer-display-feature-text-message").get_text()

               if product_price_span:
                  product_price_span = product_price_span.replace(",", "")
                  product_price_pattern = r'\d+.\d+'
                  matches = re.findall(product_price_pattern, product_price_span)
                  if matches:
                     price = matches[0].split(".")[0]
                     product_price = int(price)

                  else:
                     product_price = None

               scraped_data.append({
                  "agent": agent, 
                  "time": formatted_time, 
                  "date": formatted_date, 
                  "url": url, 
                  "prod_title": product_title_span, 
                  "price": product_price, 
                  "seller": seller
               })
               
               with open("scraped_data.json", "w", encoding='utf-8') as json_file:
                  json.dump(scraped_data, json_file, indent=3)
            except Exception as e:
               print(f'Got exception while scraping the data {repr(e)}')

               if retry_count < max_retries:
                  print("Retrying...")
                  return scrape(url, max_retries, retry_count + 1)
               else:
                  print(f"Max retries exceeded for URL: {url}")
                  return {
                     "agent": agent, 
                     "time": formatted_time, 
                     "date": formatted_date, 
                     "url": url, 
                     "prod_title": "not found", 
                     "price": "not found", 
                     "seller": "not found"
                  }
            # return jsonify(scrapper)
         
         else:
            # If credits are insufficient, repick another scrapper
            return scrape(url, retry_count + 1)  # Recursive call to repick
            # continue
   for url in urls:
      scrape(url)

   return jsonify(scraped_data)


@app.route('/noon', methods=['POST'])
def noon():
   try:
      driver = webdriver.Chrome(service=s, options=chrome_options)

      # Initialize an empty list to store scraped data
      scraped_data = []
      data = request.json

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
         # html2 = r"{html_content}"
         # html = html_content+"\\".replace(r"\\", "")


         # Parse the HTML content using Beautiful Soup
         soup = BeautifulSoup(html_content, "html.parser")
         # with open("noon.html", "w") as a:
         #  json.dump(html, a)

         # Extract relevant information from the page (customize this part)
         title = soup.find("title").get_text() if soup.find("title") else None
         product_title_span = soup.select_one("div.QNRMo > h1").get_text() if soup.select_one("div.QNRMo > h1") else None
         product_price_span = soup.find("div",class_="priceNow") if soup.find("div",class_="priceNow") else None
         product_seller_span = soup.find("div",class_="bAFCnA").get_text() if soup.find("div",class_="bAFCnA") else None
         date = datetime.date.today()
         formatted_date = date.strftime("%d-%m-%Y")
         time = datetime.datetime.now().time()
         formatted_time = time.strftime("%I:%M:%S %p")
         if product_price_span:
                    product_price_class = product_price_span.get_text()
                  #   product_price_class = product_price_class.replace(",", "")
                    product_price_pattern = r'\d+\.\d+'
                    matches = re.findall(product_price_pattern, product_price_class)
                    if matches:
                        product_price = float(matches[0])
                    else:
                        product_price = None

         # Append the scraped data to the list
         scraped_data.append({"time": formatted_time, "date": formatted_date, "title":title, "url": url, "prod_title": product_title_span, "price": product_price, "seller": product_seller_span})
         with open("scraped_data.json", "w") as json_file:
          json.dump(scraped_data, json_file, indent=3)
      # Save the scraped data to a JSON file
      
         
      driver.quit()  # Close the browser
      # return jsonify({"scraped_data": scraped_data})

      scrape_data = [{'asin': asin, 'url': url} for asin, url in zip(asins, urls)]

      with open('noon.json', 'w') as f:
         json.dump(scrape_data, f, indent=3)

      # return jsonify({"message": "Noon Data Scraped Successfully!"})
      return jsonify({"scraped_data": scraped_data})
   except Exception as e:
      return jsonify({'error': str(e)}), 500


@app.route('/jumia', methods=['POST'])
def jumia():
    try:
        scraped_data = []  # Initialize an empty list to store scraped data
        data = request.json

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

      #   return jsonify({"message": "Jumia Data Scraped Successfully!"})
        return jsonify({"scraped_data": scraped_data})


    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/btech', methods=['POST'])
def btech():
   try:
      driver = webdriver.Chrome(service=s, options=chrome_options)

      scraped_data = []  # Initialize an empty list to store scraped data
      data = request.json

      if not isinstance(data, list):
         return jsonify({'error': 'Invalid JSON format. Expecting an array of objects.'}), 400
      
      skus = [item.get('sku') for item in data]
      urls = [item.get('url') for item in data]

      if None in urls or None in skus:
         return jsonify({'error': 'Each object in the array must have "platform" and "sku" keys.'}), 400

      if len(urls) != len(skus):
         return jsonify({'error': 'Number of platforms must match number of skus'}), 400

      for url in urls:
         driver.get(url)
         html_content = driver.page_source
         # response = requests.get(url)

         soup = BeautifulSoup(html_content, "html.parser")
         with open("btech.html", "w") as f:
            f.write(html_content) 

         prod_title = soup.find("span", class_="base").text.strip()
         prod_price = soup.find("span", {"id": lambda x: x and "product-price" in x})["data-price-amount"]
         # prod_seller = soup.find("span", class_="seller-name").text.strip()
         prod_seller = soup.select_one("div.seller-custom-inner").get_text()

         date = datetime.date.today()
         formatted_date = date.strftime("%d-%m-%Y")
         time = datetime.datetime.now().time()
         formatted_time = time.strftime("%I:%M:%S %p")

         # Append the scraped data to the list
         scraped_data.append({"date": formatted_date, "time": formatted_time, "url": url, "product title": prod_title, "price": prod_price, "seller": prod_seller})
         with open("scraped_data.json", "w") as json_file:
            json.dump(scraped_data, json_file, indent=3)

         driver.quit()

      btech_data = [{'platform': "B.TECH", 'sku': sku, 'URL': url} for url, sku in zip(urls, skus)]
      with open('btech.json', 'w') as f:
         json.dump(btech_data, f)

      # return jsonify({'message': 'Data Received!'})
      return jsonify({"scraped_data": scraped_data})


   except Exception as e:
      return jsonify({'error': str(e)}), 500


# @app.route('/scrape', methods=['GET'])
# def scrape():
#    try:

#       # chrome_options = webdriver.ChromeOptions()
#       # chrome_options.add_argument("--headless")
#       # chrome_options.add_argument("--remote-debugging-port=9222")
#       # s = webdriver.ChromeService(executable_path=binary_path)
#       driver = webdriver.Chrome(service=s, options=chrome_options)

#       # Initialize an empty list to store scraped data
#       scraped_data = []
#       data = request.get_json()

#       if not isinstance(data, list):
#          return jsonify({'error': 'Invalid JSON format. Expecting an array of objects.'}), 400

#       asins = [item.get('asin') for item in data]
#       urls = [item.get('url') for item in data]

#       if None in asins or None in urls:
#          return jsonify({'error': 'Each object in the array must have "asin" and "url" keys.'}), 400

#       if len(asins) != len(urls):
#          return jsonify({'error': 'Number of ASINs must match the number of URLs'}), 400
      
#       # original_array = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
#       split_urls = split_array(urls)
      
#       results = []
#       # def scrape_url(url):
#       #       # r = requests.get(url)
#       #       driver.get(url)  # Open the URL in the browser
#       #       html_content = driver.page_source  # Get the HTML content

#       #       soup = BeautifulSoup(html_content, "html.parser")
#       #       title = soup.find("title").text.strip()
#       #       # product_title_span = soup.find("span", id="productTitle").text.strip()
#       #       product_price_span = soup.find("span", class_="-fs24").text.strip()
#       #       # product_seller_span = soup.find("span", class_="offer-display-feature-text-message").text.strip()
#       #       date = datetime.date.today()
#       #       formatted_date = date.strftime("%d-%m-%Y")
#       #       time = datetime.datetime.now().time()
#       #       formatted_time = time.strftime("%I:%M:%S %p")
#       #       results.append({"date": formatted_date, "time": formatted_time, "url": url, "title": title, "price": product_price_span})
#       #       with open("scraped_data.json", "w") as json_file:
#       #          json.dump(results, json_file, indent=3)
#       #       # return {"date": formatted_date, "time": formatted_time, "url": url, "title": title}
#       #       return

#         # Use ThreadPoolExecutor to run scrape_url concurrently
#       # with ThreadPoolExecutor(max_workers=10) as executor:
#       #    futures = [executor.submit(scrape_url, url) for url in urls]

#       # results = [future.result() for future in futures]

#       def scrape_urls(url_list):
#          for url in url_list:
#             driver.get(url)  # Open the URL in the browser
#             html_content = driver.page_source  # Get the HTML content

#             soup = BeautifulSoup(html_content, "html.parser")
#             title = soup.find("title").text.strip()
#             product_price_span = soup.find("span", class_="-fs24").text.strip()

#             date = datetime.date.today()
#             formatted_date = date.strftime("%d-%m-%Y")
#             time = datetime.datetime.now().time()
#             formatted_time = time.strftime("%I:%M:%S %p")

#             results.append({"date": formatted_date, "time": formatted_time, "url": url, "title": title, "price": product_price_span})

#          with open("scraped_data.json", "w") as json_file:
#             json.dump(results, json_file, indent=3)
         
#          return


#       with concurrent.futures.ThreadPoolExecutor(max_workers=len(urls)) as executor:
#          # Submit tasks and collect futures
#          future_to_url = {executor.submit(scrape_urls, url_listaya): url_listaya for url_listaya in split_urls}
#          for future in concurrent.futures.as_completed(future_to_url):
#             url = future_to_url[future]
#             try:
#                result = future.result()
#                # results.append(result)
#             except Exception as e:
#                print(f"Error scraping {url}: {e}")

#       # Save results to a JSON file
#       # with open("scraped_data.json", "w") as json_file:
#       #    json.dump(results, json_file, indent=3)
      
         
#       driver.quit()  # Close the browser
#       # scrape_data = [{'asin': asin, 'url': url} for asin, url in zip(asins, urls)]

#       # with open('amazon.json', 'w') as f:
#       #    json.dump(scrape_data, f, indent=3)

#       return jsonify({"message": "Amazon Data Scraped Successfully!"})

#    except Exception as e:
#       return jsonify({'error': str(e)}), 500
   

@app.route('/scrape', methods=['GET'])
def scrape():
   try:

      def scrape_urls(url, results_queue):
         # for url in url_list:
            driver = webdriver.Chrome(service=s, options=chrome_options)
            
            driver.get(url)  # Open the URL in the browser
            html_content = driver.page_source  # Get the HTML content

            soup = BeautifulSoup(html_content, "html.parser")
            title = soup.find("title").text.strip()
            product_price_span = soup.find("span", class_="-fs24").text.strip()

            date = datetime.date.today()
            formatted_date = date.strftime("%d-%m-%Y")
            time = datetime.datetime.now().time()
            formatted_time = time.strftime("%I:%M:%S %p")

            results_queue.put({"date": formatted_date, "time": formatted_time, "url": url, "title": title, "price": product_price_span})
            driver.quit()

            return

      # driver = webdriver.Chrome(service=s, options=chrome_options)

      data = request.get_json()

      if not isinstance(data, list):
         return jsonify({'error': 'Invalid JSON format. Expecting an array of objects.'}), 400

      asins = [item.get('asin') for item in data]
      urls = [item.get('url') for item in data]

      if None in asins or None in urls:
         return jsonify({'error': 'Each object in the array must have "asin" and "url" keys.'}), 400

      if len(asins) != len(urls):
         return jsonify({'error': 'Number of ASINs must match the number of URLs'}), 400

      results_queue = queue.Queue()
      threads = []

      for url in urls:
         thread = threading.Thread(target=scrape_urls, args=(url, results_queue))
         thread.start()
         threads.append(thread)

      split_urls = split_array(urls)

      # for url_list in split_urls:
      #    thread = threading.Thread(target=scrape_urls, args=(url_list, results_queue))
      #    thread.start()
      #    threads.append(thread)

        # Wait for all threads to finish
      for thread in threads:
            thread.join()

        # Gather results from the queue
      results = []
      while not results_queue.empty():
            results.append(results_queue.get())

      with open("scraped_data.json", "w") as json_file:
            json.dump(results, json_file, indent=3)

      # driver.quit()

      return jsonify({"message": "Amazon Data Scraped Successfully!"})

   except Exception as e:
      return jsonify({'error': str(e)}), 500
   
valid_proxies = []

def get_proxies():
   with open("valid_proxies.txt", "r") as f:
      proxies = f.read().split("\n")
      for proxy in proxies:
         valid_proxies.append(proxy)


# def get_proxies():
#    with open("valid_proxies.txt", "r") as f:
#       proxies = f.read().split("\n")
#       for p in proxies:
#          q.put(p)

@app.route('/scrape3', methods=['GET'])
def scrape3():

   get_proxies()
   scraped_data = []
   data = request.get_json()
   if not isinstance(data, list):
      return jsonify({'error': 'Invalid JSON format. Expecting an array of objects.'}), 400

   asins = [item.get('sku') for item in data]
   urls = [item.get('url') for item in data]

   if None in asins or None in urls:
      return jsonify({'error': 'Each object in the array must have "asin" and "url" keys.'}), 400

   if len(urls) > 100:
      return jsonify({'error': 'Too Many Products, Max is 100.'}), 400

   if len(asins) != len(urls):
      return jsonify({'error': 'Number of ASINs must match the number of URLs'}), 400

   # proxy_index = random.randint(0, len(valid_proxies)-1)
   proxy = random.choice(valid_proxies)
   while proxy == "":
      proxy = random.choice(valid_proxies)

   # global q
   # while not q.empty():
   #    proxy = q.get()
   try:
      print(proxy)
      chrome_options.add_argument(f"--proxy-server=https://{proxy}")
      driver = webdriver.Chrome(service=s, options=chrome_options)

      for url in urls:
         driver.get(url)  # Open the URL in the browser
         html_content = driver.page_source  # Get the HTML content

            # Parse the HTML content using Beautiful Soup
         soup = BeautifulSoup(html_content, "html.parser")

         prod_title = soup.find("span", class_="base").text.strip()
         # prod_price = soup.find("span", class_="price").text.strip()
         prod_price = soup.find("span", class_="price").text.strip()
         prod_seller = soup.find("a", class_="gtm-open-seller-page").text.strip()
         # prod_seller = soup.find("span", class_="normal-text").text.strip()

         date = datetime.date.today()
         formatted_date = date.strftime("%d-%m-%Y")
         time = datetime.datetime.now().time()
         formatted_time = time.strftime("%I:%M:%S %p")

         # Append the scraped data to the list
         scraped_data.append({"date": formatted_date, "time": formatted_time, "from ip": proxy, "url": url, "product title": prod_title, "price": prod_price, "seller": prod_seller})
         with open("scraped_data.json", "w") as json_file:
            json.dump(scraped_data, json_file, indent=3)
         # Save the scraped data to a JSON file
         
            
      driver.quit()  # Close the browser
      # scrape_data = [{'asin': asin, 'url': url} for asin, url in zip(asins, urls)]

      # with open('amazon.json', 'w') as f:
      #    json.dump(scrape_data, f, indent=3)

      return jsonify({"message": "Amazon Data Scraped Successfully!"})
   except Exception as e:
      return jsonify({'error': str(e)}), 500
      # continue

def get_scrappers():
   with open("scrappers.json", 'r') as json_file:
      data = json.load(json_file)
      return data

@app.route('/scrapeAmazon', methods=['GET'])
def scrapeAmazon():

   scraped_data = []
   data = request.get_json()
   if not isinstance(data, list):
      return jsonify({'error': 'Invalid JSON format. Expecting an array of objects.'}), 400

   asins = [item.get('asin') for item in data]
   urls = [item.get('url') for item in data]

   if None in asins or None in urls:
      return jsonify({'error': 'Each object in the array must have "asin" and "url" keys.'}), 400

   if len(urls) > 100:
      return jsonify({'error': 'Too Many Products, Max is 100.'}), 400

   if len(asins) != len(urls):
      return jsonify({'error': 'Number of ASINs must match the number of URLs'}), 400
   
   def scrape(url):
         
         scrappers = get_scrappers()
         scrapper = random.choice(scrappers)
         # Find the index of the original scrapper
         original_index = scrappers.index(scrapper)

         if scrapper["credits"] >= scrapper["deductible"]:
            if scrapper["service"] == "scrapingant":
               agent = "scrapingAnt"
               print(scrapper)
               try:
                  client = ScrapingAntClient(token=f"{scrapper['api_key']}")
                  result = client.general_request(
                     url,
                     browser=True,
                     return_page_source=True
                     # ,block_resource='image'
                  )
                  scrapper["credits"] -= scrapper["deductible"]
                  scrappers[original_index] = scrapper
                  html_content = result.content
               except Exception as e:
                  print(f'Got exception while parsing data {repr(e)}')
                  return scrape(url)

            elif scrapper["service"] == "scrapingdog":
               print(scrapper)
               agent = "scrapingdog"
               params = {
                  "api_key": f"{scrapper['api_key']}",
                  "url": url,
                  "dynamic": "true",
               }
               try:

                  response = requests.get(f"{scrapper['service_url']}", params=params)
                  scrapper["credits"] -= scrapper["deductible"]
                  scrappers[original_index] = scrapper

                  html_content = response.text
               except Exception as e:
                  print(f'Got exception while parsing data {repr(e)}')
                  return scrape(url)
               # return(response.text)
            with open("scrappers.json", "w") as json_file:
               json.dump(scrappers, json_file, indent=3)

            try:
               # Parse the HTML content using Beautiful Soup
               soup = BeautifulSoup(html_content, "html.parser")

               product_title_span = soup.find("span", id="productTitle").text.strip()
               product_price_span = soup.find("span", id="tp_price_block_total_price_ww").text.strip()
               # product_seller_span = soup.find("span", class_="offer-display-feature-text-message").text.strip()
               product_seller_span = soup.find("a", id="sellerProfileTriggerId")
               if(product_seller_span):
                  seller = product_seller_span.text.strip()
               else:
                  seller = soup.select_one("div.offer-display-feature-text > span.offer-display-feature-text-message").get_text()

               date = datetime.date.today()
               formatted_date = date.strftime("%d-%m-%Y")
               time = datetime.datetime.now().time()
               formatted_time = time.strftime("%I:%M:%S %p")
               if product_price_span:
                        #   product_price_class = product_price_span
                  product_price_span = product_price_span.replace(",", "")
                        # print(product_price_span)
                  product_price_pattern = r'\d+.\d+'
                  matches = re.findall(product_price_pattern, product_price_span)
                  if matches:
                     price = matches[0].split(".")[0]
                     product_price = int(price)

                  else:
                     product_price = None

               # Append the scraped data to the list
               scraped_data.append(
                  {
                     "agent": agent, 
                     "time": formatted_time, 
                     "date": formatted_date, 
                     "url": url, 
                     "prod_title": product_title_span, 
                     "price": product_price, 
                     "seller": seller
                  })
               
               with open("scraped_data.json", "w") as json_file:
                  json.dump(scraped_data, json_file, indent=3)
            except Exception as e:
               print(f'Got exception while scraping the data {repr(e)}')
               return scrape(url)
            # return jsonify(scrapper)
         
         else:
            # If credits are insufficient, repick another scrapper
            return scrape(url)  # Recursive call to repick
            # continue
   for url in urls:
      scrape(url)

   return jsonify(scraped_data)
   
   
         

   # print(scrapper)

      
   # threads = []
   # # for _ in range(10):
   # for url in urls:
   #    t = threading.Thread(target=scrape, args=[urls])
   #    t.start()
   #    threads.append(t)
   # # check_proxies()
   # for t in threads:
   #    t.join()
   # with open("scraped_data.json", "w") as json_file:
   #    json.dump(scraped_data, json_file, indent=3)
   # max_retries = 5
   # with concurrent.futures.ThreadPoolExecutor() as executor:
   #    executor.map(scrape, urls)
        # Submit each URL to the executor
      #    futures = [executor.submit(scrape, url) for url in urls]

      #   # Retrieve results from completed futures
      #    for future in concurrent.futures.as_completed(futures):
      #       retries = 0
      #       while retries < max_retries:
      #             try:
      #                result = future.result()
      #                scraped_data.append(result)
      #                break  # Successfully scraped, break out of the retry loop
      #             except Exception as e:
      #                print(f"Scraping error: {e}")
      #                retries += 1
      #                print(f"Retrying ({retries}/{max_retries})...")

      #       if retries == max_retries:
      #             print(f"Max retries reached. Unable to scrape data for URL")


# @app.route('/scrapeAmazon', methods=['GET'])
# def scrapeAmazon():

#    scraped_data = []
#    data = request.get_json()
#    if not isinstance(data, list):
#       return jsonify({'error': 'Invalid JSON format. Expecting an array of objects.'}), 400

#    asins = [item.get('asin') for item in data]
#    urls = [item.get('url') for item in data]

#    if None in asins or None in urls:
#       return jsonify({'error': 'Each object in the array must have "asin" and "url" keys.'}), 400

#    if len(urls) > 100:
#       return jsonify({'error': 'Too Many Products, Max is 100.'}), 400

#    if len(asins) != len(urls):
#       return jsonify({'error': 'Number of ASINs must match the number of URLs'}), 400
#    for url in urls:

#       scrappers = get_scrappers()
#       scrapper = random.choice(scrappers)
#       original_index = scrappers.index(scrapper)

#       if scrapper["credits"] >= scrapper["deductible"]:
#          if scrapper["service"] == "scrapingant":
#             client = ScrapingAntClient(token=f"{scrapper['api_key']}")
#             result = client.general_request(
#                url,
#                browser=True,
#                return_page_source=True
#             )

#             scrapper["credits"] -= scrapper["deductible"]
#             scrappers[original_index] = scrapper
#             print(scrapper)
#             html_content = result.content

#          elif scrapper["service"] == "scrapingdog":

#             params = {
#                "url": url,
#                "dynamic": "true",
#                "api_key": f"{scrapper['api_key']}"
#             }

#             response = requests.get(f"{scrapper['service_url']}", params=params)

#             scrapper["credits"] -= scrapper["deductible"]
#             scrappers[original_index] = scrapper
#             print(scrapper)
#             html_content = response.text
#          with open("scrappers.json", "w") as json_file:
#             json.dump(scrappers, json_file, indent=3)
#          soup = BeautifulSoup(html_content, "html.parser")

#          product_title_span = soup.find("span", id="productTitle").text.strip()
#          product_price_span = soup.find("span", class_="a-price-whole").text.strip()
#          product_seller_span = soup.find("span", class_="offer-display-feature-text-message").text.strip()
#          date = datetime.date.today()
#          formatted_date = date.strftime("%d-%m-%Y")
#          time = datetime.datetime.now().time()
#          formatted_time = time.strftime("%I:%M:%S %p")

#          scraped_data.append({ 
#             "date": formatted_date, 
#             "time": formatted_time, 
#             "url": url, 
#             "prod_title": product_title_span, 
#             "price": product_price_span, 
#             "seller": product_seller_span 
#          })
         
#          with open("scraped_data.json", "w") as json_file:
#             json.dump(scraped_data, json_file, indent=3)

#       else:
#          continue

#    return jsonify(scraped_data)

@app.route('/test', methods=['GET'])
def test():

   original_array = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
   result_array = split_array(original_array)
   print(result_array)
   return jsonify(result_array)

# @celery.task
# def schedule_tasks():
#    schedule.every().day.at("10:30").do(prepare)
#    schedule.every().day.at("10:45").do(prepare)
#    schedule.every().day.at("11:00").do(prepare)
#    schedule.every().day.at("11:15").do(prepare)

#    while True:
#       schedule.run_pending()
#       time.sleep(10)

if __name__ == '__main__':
   # executor = ThreadPoolExecutor(max_workers=1)
   # executor.submit(schedule_tasks)
   # schedule_tasks()

   app.run(host='0.0.0.0', port=5000, debug=True)
