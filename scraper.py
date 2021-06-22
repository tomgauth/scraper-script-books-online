import requests
from bs4 import BeautifulSoup
import re
import csv
import os
from urllib.parse import urljoin

# scrape a book page

base = 'http://books.toscrape.com'
base_catalogue = base +'/catalogue'
# url = "http://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html"

def scrape_book_page(url):

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

# add_row([
#   product_page_url,
#   universal_product_code,
#   title,
#   price_including_tax,
#   price_excluding_tax,
#   number_available,
#   product_description,
#   category,
#   review_rating,
#   image_url
#   ])


# scrape a category

# get all the elements 'article' class:'product_pod'

# TODO REFACTO - USE CLASSES?


# gets the category url in input
# returns a list of url of product pages

category_url = 'https://books.toscrape.com/catalogue/category/books/historical-fiction_4/'

def get_category_pages(category_url):
  # repeat for each page
  # if the page is full, check if there are more books
  response = requests.get(category_url)
  soup = BeautifulSoup(response.content, 'html.parser')
  raw_html_books = soup.find_all('article', class_='product_pod')
  page_urls = []
  if len(raw_html_books) != 20:
    page_urls.append(category_url)
  else:
    n = 1
    while response.status_code == 200:
      page_url = category_url+'page-{}.html'.format(n)
      response = requests.get(page_url)
      n += 1
      page_urls.append(page_url)
  # last url appended will be leading to a 404 page
    page_urls.pop()
  return page_urls




def scrape_category_page(page_url):
  response = requests.get(category_url)
  soup = BeautifulSoup(response.content, 'html.parser')
  raw_html_books = soup.find_all('article', class_='product_pod')
  # append the product page url to a list
  product_page_urls = []
  for b in raw_html_books:
    prod_page_path = b.find('a')['href']
    prod_page_url_end = re.findall("(?<=../../..)[^\]]+",prod_page_path)[0]
    prod_page_url = base_catalogue + prod_page_url_end
    product_page_urls.append(prod_page_url)
  return product_page_urls

# loop through each category

# get the html of the base url

def scrape_categories(base):
  response = requests.get(base)
  soup = BeautifulSoup(response.content, 'html.parser')
  div_categories = soup.find('div', class_='side_categories')
  category_paths = div_categories.find_all('a')
  categories = []
  for category_path in category_paths:
    print(category_path['href'])
    print(base)
    print(base_catalogue)
    category_url = base + '/' + category_path['href']
    categories.append(category_url)
  return categories


def scrape_all():
  categories = scrape_categories(base)
  for cat in categories:
    book_page_urls = get_category_pages(cat)
    for book_page in book_page_urls:
      product_page_urls = scrape_category_page(book_page)
      for product_page in product_page_urls:
        print(product_page)
        scrape_book_page(product_page)




