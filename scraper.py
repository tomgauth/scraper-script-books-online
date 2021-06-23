import requests
from bs4 import BeautifulSoup
import re
import csv
import os
from urllib.parse import urljoin


def main():


  base = 'http://books.toscrape.com'
  base_catalogue = base +'/catalogue'


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

  def add_row(row):
    file = create_csv()
    f = open(csv_file, 'a')
    writer = csv.writer(f)
    writer.writerow(row)
    f.close()
    print('Inserted: ')
    for cell in row:
      print(cell)


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

    review_rating = num_stars(soup)

    image_path = soup.find('img')['src']
    image_path_short = re.findall("(?<=../..)[^\]]+",image_path)[0]
    image_url = base + image_path_short

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


  def get_category_pages(category_url):
    response = requests.get(category_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    raw_html_books = soup.find_all('article', class_='product_pod')
    page_urls = []
    if len(raw_html_books) != 20:
      page_urls.append(category_url)
    else:
      n = 1
      while response.status_code == 200:
        print(n)
        category_url = re.sub(r'index.html','',category_url)
        page_url = category_url+'page-{}.html'.format(n)
        print(page_url)
        response = requests.get(page_url)
        print(response.status_code)
        page_urls.append(page_url)
        print(page_urls)
        n += 1
      page_urls.pop()
    return page_urls


  def scrape_category_page(page_url):
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
      print(category_path['href'])
      print(base)
      print(base_catalogue)
      category_url = base + '/' + category_path['href']
      print('category url: ' + category_url)
      categories.append(category_url)
    categories.remove('http://books.toscrape.com/catalogue/category/books_1/index.html')
    return categories


  def scrape_all():
    categories = scrape_categories(base)
    category_pages_urls = []
    product_page_urls = []
    for cat in categories:
      category_pages_urls += get_category_pages(cat)
      for category_page_url in category_pages_urls:
        product_page_urls += scrape_category_page(category_page_url)
        print(len(product_page_urls),'/1000')
        for product_page in product_page_urls:
          print('PRODUCT PAGE: ',product_page)
          scrape_book_page(product_page)



if __name__ == "__main__":
  main()

