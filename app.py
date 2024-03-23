import os
import re
import json
import time
import queue
import requests
import datetime
# import schedule
import threading
import subprocess
import concurrent.futures
# from check_proxies import prepare
from bs4 import BeautifulSoup
from selenium import webdriver
from chromedriver_py import binary_path
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--remote-debugging-port=9222")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36")  # Set user-agent header
s = webdriver.ChromeService(executable_path=binary_path)
q = queue.Queue()

def get_proxies():
   with open("valid_proxies.txt", "r") as f:
      proxies = f.read().split("\n")
      for p in proxies:
         q.put(p)

# def run_other_script():
#     subprocess.run(["python", "check_proxies.py"])

# def run_check_proxies():
#     # Option 1: Run the check_proxies.py script
#    #  import subprocess
#    #  subprocess.run(["python", "check_proxies.py"])

#     # Option 2: Run the prepare() function from check_proxies.py
#     # from check_proxies import prepare
#     prepare()

# def schedule_check_proxies():
#     schedule.every(2).minutes.do(run_check_proxies)

#     while True:
#         schedule.run_pending()
#         time.sleep(60)  # Sleep for 1 minute before checking for scheduled jobs again

# # Uncomment the line below to start scheduling the check_proxies job
# schedule_check_proxies()

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

@app.route('/amazon', methods=['POST'])
def amazon():
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
         if product_price_span:
                  #   product_price_class = product_price_span
                    product_price_span = product_price_span.replace(",", "")
                    print(product_price_span)
                    product_price_pattern = r'\d+.\d+'
                    matches = re.findall(product_price_pattern, product_price_span)
                    if matches:
                        product_price = float(matches[0])
                    else:
                        product_price = None

         # Append the scraped data to the list
         scraped_data.append({"time": formatted_time, "date": formatted_date, "url": url, "prod_title": product_title_span, "price": product_price, "seller": product_seller_span})
         with open("scraped_data.json", "w") as json_file:
          json.dump(scraped_data, json_file, indent=3)
      # Save the scraped data to a JSON file
      
      
      driver.quit()  # Close the browser
      scrape_data = [{'asin': asin, 'url': url} for asin, url in zip(asins, urls)]

      # return jsonify({"scraped_data": scraped_data})


      with open('amazon.json', 'w') as f:
         json.dump(scrape_data, f, indent=3)

      # return jsonify({"message": "Amazon Data Scraped Successfully!"})
      return jsonify({"scraped_data": scraped_data})


   except Exception as e:
      return jsonify({'error': str(e)}), 500
# import requests

# @app.route('/amazon', methods=['POST'])
# def amazon():
#     try:
#         driver = webdriver.Chrome(service=s, options=chrome_options)

#         # Initialize an empty list to store scraped data
#         scraped_data = []
#         data = request.json

#         if not isinstance(data, list):
#             return jsonify({'error': 'Invalid JSON format. Expecting an array of objects.'}), 400

#         asins = [item.get('asin') for item in data]
#         urls = [item.get('url') for item in data]

#         if None in asins or None in urls:
#             return jsonify({'error': 'Each object in the array must have "asin" and "url" keys.'}), 400

#         if len(asins) != len(urls):
#             return jsonify({'error': 'Number of ASINs must match the number of URLs'}), 400

#         for url in urls:
#             driver.get(url)  # Open the URL in the browser
#             html_content = driver.page_source  # Get the HTML content

#             # Parse the HTML content using Beautiful Soup
#             soup = BeautifulSoup(html_content, "html.parser")

#             # Extract relevant information from the page (customize this part)
#             # title = soup.find("title").text.strip()
#             product_title_span = soup.find("span", id="productTitle").text.strip()
#             product_price_span = soup.find("span", class_="a-price-whole").text.strip()
#             product_seller_span = soup.find("span", class_="offer-display-feature-text-message").text.strip()
#             date = datetime.date.today()
#             formatted_date = date.strftime("%d-%m-%Y")
#             time = datetime.datetime.now().time()
#             formatted_time = time.strftime("%I:%M:%S %p")

#             # Append the scraped data to the list
#             scraped_data.append({"time": formatted_time, "date": formatted_date, "url": url, "prod_title": product_title_span, "price": product_price_span, "seller": product_seller_span})

#         # Close the browser
#         driver.quit()

#         # Save the scraped data to a JSON file
#         with open("scraped_data.json", "w") as json_file:
#             json.dump(scraped_data, json_file, indent=3)

#         # Send the scraped data to the Laravel backend

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

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
   

@app.route('/scrape3', methods=['GET'])
def scrape3():
   scraped_data = []
   data = request.get_json()
   global q
   while not q.empty():
      proxy = q.get()
      try:
         # start_time = time.time()
         # res = requests.get("http://ipinfo.io/json",
         #                    proxies = { "http": proxy,
         #                                "https": proxy},
         #                   timeout=5)
         # elapsed_time = time.time() - start_time
         driver = webdriver.Chrome(service=s, options=chrome_options)

         # Initialize an empty list to store scraped data


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
      except:
         continue
   # try:


   # except Exception as e:
   #    return jsonify({'error': str(e)}), 500


@app.route('/test', methods=['GET'])
def test():

   original_array = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
   result_array = split_array(original_array)
   print(result_array)
   return jsonify(result_array)



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