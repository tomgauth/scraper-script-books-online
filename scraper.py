import requests
from bs4 import BeautifulSoup
import re
import csv
import os
from pathlib import Path
from urllib.parse import urljoin



def create_csv(csv_name):
  # check if file is already created
  path = f'./extracted data/csv files/{csv_name}.csv'
  p = Path(path)
  if not p.is_file():
    f = open(path, 'w')
    writer = csv.writer(f)
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
    f.close()
  return path


def num_stars(soup):
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

def add_row(file_path, row):
  with open(file_path, 'a', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(row)
  f.close()
  print('row added')


def download_book_img(numbered_category_name, book_title, image_url):
  # create a folder named after the category
  path = f"extracted data/book images/{numbered_category_name}"
  Path(path).mkdir(parents=True, exist_ok=True)
  r = requests.get(image_url, allow_redirects=True)

  open(f'{path}/{book_title}.jpg', 'wb').write(r.content)



def scrape_book_url(url):

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
  try:
    product_description = div_header_prod_desc[0].next_sibling.next_sibling.get_text()
  except:
    print('no product_description')
    product_description = ''

  breadcrumb = soup.find("ul", {"class": "breadcrumb"})
  category_html = breadcrumb.find_all('a')[2]
  category_name = category_html.get_text().lower()
  category_href = category_html['href']
  category_num = get_cat_num(category_href)
  numbered_category_name = category_num + ' - ' + category_name
  print(numbered_category_name)
  review_rating = num_stars(soup)

  image_path = soup.find('img')['src']
  image_path_short = re.findall("(?<=../..)[^\]]+",image_path)[0]
  image_url = base + image_path_short

  file_path = create_csv(numbered_category_name)
  row = [
    product_page_url,
    universal_product_code,
    title,
    price_including_tax,
    price_excluding_tax,
    number_available,
    product_description,
    category_name, # category
    review_rating,
    image_url
  ]

  return [file_path, row, numbered_category_name]



def list_category_pages(category_url):
  response = requests.get(category_url)
  soup = BeautifulSoup(response.content, 'html.parser')
  raw_html_books = soup.find_all('article', class_='product_pod')
  page_urls = []
  if len(raw_html_books) != 20:
    page_urls.append(category_url)
  else:
    n = 1
    while response.status_code == 200:
      category_url = re.sub(r'index.html','',category_url)
      page_url = category_url+'page-{}.html'.format(n)
      response = requests.get(page_url)
      page_urls.append(page_url)
      n += 1
    page_urls.pop()
  return page_urls


def list_books_urls(page_url):
  response = requests.get(page_url)
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

def scrape_categories(base):
  response = requests.get(base)
  soup = BeautifulSoup(response.content, 'html.parser')
  div_categories = soup.find('div', class_='side_categories')
  category_paths = div_categories.find_all('a')
  categories = []
  for category_path in category_paths:
    category_url = base + '/' + category_path['href']
    categories.append(category_url)
  # TODO change this, not flexible enough
  categories.remove('http://books.toscrape.com/catalogue/category/books_1/index.html')
  return categories


def get_cat_name(category_url):
  pattern = r"category\/books\/(.+)_\d+\/index.html"
  cat_name_search = re.search(pattern, category_url, re.IGNORECASE)
  cat_name = cat_name_search.group(1)
  return cat_name

def get_cat_num(category_url):
  pattern = r"category\/books\/.+_(\d+)\/index.html"
  cat_num_search = re.search(pattern, category_url, re.IGNORECASE)
  cat_num = cat_num_search.group(1)
  return cat_num

base = 'http://books.toscrape.com'
base_catalogue = base +'/catalogue'

def main():
  # create a folder 'extracted data'
  # create a sub-folder 'csv files'
  Path("./extracted data/csv files").mkdir(parents=True, exist_ok=True)
  # create a sub-folder 'book images'
  Path("./extracted data/book images").mkdir(parents=True, exist_ok=True)
  # get the list of categories from the base
  categories_url = scrape_categories(base)
  # for each category in categories:
  for category_url in categories_url:
  # create a csv file in the folder 'csv files' name category.csv
    category_name = get_cat_name(category_url)
    category_num = get_cat_num(category_url) #get the category name from url
    pages = list_category_pages(category_url)
    print('category: ', category_name)
    for page in pages:
      books_on_page = list_books_urls(page)
      for book_url in books_on_page:
        print('current book: ', book_url)
        data = scrape_book_url(book_url)
        add_row(data[0],data[1])
        download_book_img(data[2], data[1][2], data[1][9])




if __name__ == "__main__":
  print(__name__)
  main()



# Path("./extracted data/csv files").mkdir(parents=True, exist_ok=True)
# Path("./extracted data/book images").mkdir(parents=True, exist_ok=True)
# categories_url = scrape_categories(base)
# category_url = categories_url[8]
# category_name = get_cat_name(category_url)
# create_csv(category_name)
# pages = list_category_pages(category_url)
# page = pages[2]
# books_on_page = list_books_urls(page)
# book_url = books_on_page[15]
# data = scrape_book_url(book_url)
# add_row(data[0],data[1])
