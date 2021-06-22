# input the url of any page of the website

# for an item "book", get the information:
# product_page_url
# universal_ product_code (upc)
# title
# price_including_tax
# price_excluding_tax
# number_available
# product_description
# category
# review_rating
# image_url

import requests
from bs4 import BeautifulSoup
import re

url = "http://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html"

response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

table = soup.find_all('table', class_='table table-striped')[0]

product_page_url = url

universal_product_code = table.find_all('td')[0].get_text()

div_title = soup.find(class_='col-sm-6 product_main')
title = div_title.find("h1").get_text()

price_including_tax = table.find_all('td')[3].get_text()

price_excluding_tax = table.find_all('td')[2].get_text()

raw_number_available = table.find_all('td')[5].get_text()
number_available = ''.join(filter(str.isdigit, raw_number_available))

div_header_prod_desc = soup.find_all('div',
  id='product_description', class_='sub-header')
product_description = div_header_prod_desc[0].next_sibling.next_sibling.get_text()

breadcrumb = soup.find("ul", {"class": "breadcrumb"})
category = breadcrumb.find_all('a')[2].get_text()

def num_stars():
  if soup.find('p', 'star-rating One'):
    return '1'
  elif soup.find('p', 'star-rating Two'):
    return '2'
  elif soup.find('p', 'star-rating Three'):
    return '3'
  elif soup.find('p', 'star-rating Four'):
    return '4'
  elif soup.find('p', 'star-rating Five'):
    return '5'
  else:
    return 'no ratings found'



review_rating = num_stars()

image_url = soup.find('img')['src']


# create a csv file with the information as column name

# append the data to the right columns


print(
  product_page_url,
  universal_product_code,
  title,
  price_including_tax,
  price_excluding_tax,
  number_available,
  product_description,
  category,
  review_rating,
  image_url
)
