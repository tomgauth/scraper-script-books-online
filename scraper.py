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
import csv
import os.path


url = "http://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html"
base = 'http://books.toscrape.com'

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

image_path = soup.find('img')['src']
image_path_short = re.findall("(?<=../..)[^\]]+",image_path)[0]
image_url = base + image_path_short


# create a csv file with the information as column name

# TODO REFACTO THIS - THIS FUNCTION IS WEIRD

def create_csv():
  # check if file is already created
  if not os.path.isfile('csv_file.csv'):
    f = open('csv_file.csv', 'w')
    # create the csv writer
    writer = csv.writer(f)
    # write a row to the csv file
    writer.writerow(['product_page_url',
      'universal_product_code',
      'title',
      'price_including_tax',
      'price_excluding_tax',
      'number_available',
      'product_description',
      'category',
      'review_rating',
      'image_url'])
    # close the file
    f.close()
  return 'csv_file.csv'

csv_file = create_csv()
# append the data to the right columns

def add_row(row):
  file = create_csv()
  f = open(csv_file, 'a')
  writer = csv.writer(f)
  writer.writerow(row)
  f.close()
  print('Inserted: ')
  for cell in row:
    print(cell)

add_row([
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
  ])


