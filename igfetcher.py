import sys
import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36")  # Emulate Chrome user agent

# s = Service(r"C:\Users\kikoh\.cache\selenium\chromedriver\win64\121.0.6167.85\chromedriver.exe")
driver = webdriver.Chrome(options=chrome_options)

def scrape_user_data(username):
    url = f"https://www.pixwox.com/profile/{username}/"
    driver.get(url)

    try:
      checker = driver.find_element(By.CSS_SELECTOR, "div.memo")
      if checker:
         print("User not found, try again.")
         return
    
    except NoSuchElementException:

      avatar_img = driver.find_element(By.CSS_SELECTOR, "img[src*='pixwox.com']").get_attribute("src")
      user_handle = driver.find_element(By.CSS_SELECTOR, "div.username > h2").text
      display_name = driver.find_element(By.CSS_SELECTOR, "h1.fullname").text
      bio = driver.find_element(By.CSS_SELECTOR, "div.sum").text
      follower_count = driver.find_element(By.CSS_SELECTOR, "div.item_followers > div.num").text
      following_count = driver.find_element(By.CSS_SELECTOR, "div.item_following > div.num").text
      post_count = driver.find_element(By.CSS_SELECTOR, "div.item_posts > div.num").text

      print("Avatar Image:", avatar_img)
      print("User Handle:", user_handle)
      print("Display Name:", display_name)
      print("Follower Count:", follower_count)
      print("Following Count:", following_count)
      print("Post Count:", post_count)
      print("User Bio:", bio)

    driver.quit()

if len(sys.argv) != 2:
    print("Please provide a username as an argument.")
    sys.exit(1)

username = sys.argv[1]
scrape_user_data(username)
