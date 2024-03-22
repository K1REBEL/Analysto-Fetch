import threading
import queue
import time
import requests

q = queue.Queue()
valid_proxies = []

def fetch_proxies():
   api_url = "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&timeout=600&proxy_format=ipport&format=text"
   response = requests.get(api_url)
   proxy_list = response.text.split("\n")

   # Write fetched proxies to a file
   with open("proxy_list.txt", "w") as proxy_file:
      for proxy in proxy_list:
         proxy_file.write(proxy)

   print(f"{len(proxy_list)} proxies saved to 'proxy_list.txt'.")

   with open("proxy_list.txt", "r") as f:
      proxies = f.read().split("\n")
      for p in proxies:
         q.put(p)

def check_proxies():
   global q
   while not q.empty():
      proxy = q.get()
      try:
         if proxy == '':
            continue

         start_time = time.time()
         res = requests.get("http://ipinfo.io/json", proxies = { "https": proxy, "http": proxy }, timeout=5)
         elapsed_time = time.time() - start_time

      except:
         continue

      if res.status_code == 200 and elapsed_time < 0.4:
         valid_proxies.append(proxy)
         print(proxy)
      # print(valid_proxies)

# def prepare():
#    fetch_proxies()
#    for _ in range(10):
#       threading.Thread(target=check_proxies).start()

#    for t in threading.enumerate():
#       print("Hello World!")
#       print(f"{valid_proxies}" + "Hello first")
#       if t != threading.current_thread():
#          t.join()
      
def prepare():
   fetch_proxies()
   threads = []
   for _ in range(10):
      t = threading.Thread(target=check_proxies)
      t.start()
      threads.append(t)
   # check_proxies()
   for t in threads:
      t.join()

   # print(f"{valid_proxies} Hello last")
   with open("valid_proxies.txt", "w") as output_file:
      for valid_proxy in valid_proxies:
         output_file.write(valid_proxy + "\n")

   print(f"Valid proxies saved to 'valid_proxies.txt', {len(valid_proxies)} IPs")

prepare()
