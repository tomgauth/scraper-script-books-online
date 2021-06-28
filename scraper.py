import requests
from bs4 import BeautifulSoup
import re
import csv
import time
from pathlib import Path
from slugify import slugify
from progress.bar import IncrementalBar


base = 'http://books.toscrape.com'
base_catalogue = base + '/catalogue'
ascii_art = './ascii-art.txt'


def print_logo(ascii_art):
    with open(ascii_art, 'r') as f:
        # this will print each character found in ascii file very fast.
        # Makes it prettier
        for line in f:
            print(line)
            time.sleep(0.05)
    print('''⚠️   Make sure to delete or rename the \"extracted data\" folder
before running the script. Scraped data will be added but not updated.\n
ℹ️   Press ctrl+c to stop
ℹ️   Find all the scraped data in folder \"extracted data\"\n\n''')


def scrape_categories(base):
    # returns the url linking to the page 1 of each category
    # found on the main page
    response = requests.get(base)
    soup = BeautifulSoup(response.content, 'html.parser')
    div_categories = soup.find('div', class_='side_categories')
    category_paths = div_categories.find_all('a')
    categories = []
    for category_path in category_paths:
        category_url = base + '/' + category_path['href']
        categories.append(category_url)
    # TODO change this, not flexible enough
    categories.remove(
        'http://books.toscrape.com/catalogue/category/books_1/index.html')
    return categories


def count_books(base):
    # todo refacto these 2 lines into a "make_soup" function
    response = requests.get(base)
    soup = BeautifulSoup(response.content, 'html.parser')
    num_books_txt = soup.form.div.next_sibling.next_sibling.get_text()
    num_books_total = int(num_books_txt)
    return num_books_total


def get_cat_name(category_url):
    # returns the name of the category
    pattern = r"category\/books\/(.+)_\d+\/index.html"
    cat_name_search = re.search(pattern, category_url, re.IGNORECASE)
    cat_name = cat_name_search.group(1)
    return cat_name


def get_cat_num(category_url):
    # returns the number of the category, eg. 2 for Travel
    pattern = r"category\/books\/.+_(\d+)\/index.html"
    cat_num_search = re.search(pattern, category_url, re.IGNORECASE)
    cat_num = cat_num_search.group(1)
    return cat_num


def get_cat_size(category_url):
    # returns the number of books in a category based on the html div
    response = requests.get(category_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    num_books_txt = soup.form.div.next_sibling.next_sibling.get_text()
    num_books_in_cat = int(num_books_txt)
    return num_books_in_cat


def list_category_pages(category_url):
    soup = get_soup(category_url)
    raw_html_books = soup.find_all('article', class_='product_pod')
    page_urls = []
    if len(raw_html_books) != 20:
        page_urls.append(category_url)
    else:
        n = 1
        while response.status_code == 200:
            category_url = re.sub(r'index.html', '', category_url)
            page_url = category_url+'page-{}.html'.format(n)
            response = requests.get(page_url)
            page_urls.append(page_url)
            n += 1
        page_urls.pop()
    return page_urls


def get_soup(url):
    # takes a page url and returns the page html
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    except HTTPError as hp:
        print(hp)


def list_books_urls(page_url):
    # returns a list of all the book urls found on the page
    soup = get_soup(page_url)
    raw_html_books = soup.find_all('article', class_='product_pod')
    # appends the product page url to a list
    product_page_urls = []
    for b in raw_html_books:
        prod_page_path = b.find('a')['href']
        prod_page_url_end = re.findall(
            "(?<=../../..)[^\]]+", prod_page_path)[0]
        prod_page_url = base_catalogue + prod_page_url_end
        product_page_urls.append(prod_page_url)
    return product_page_urls


def scrape_book_url(url):

    soup = get_soup(url)

    try:
        table = soup.find_all('table', class_='table table-striped')[0]

        try:
            price_including_tax = table.find_all('td')[3].get_text()
        except:
            price_including_tax = ''
        try:
            universal_product_code = table.find_all('td')[0].get_text()
        except:
            universal_product_code = ''
        try:
            price_excluding_tax = table.find_all('td')[2].get_text()
        except:
            price_excluding_tax = ''
        try:
            raw_number_available = table.find_all('td')[5].get_text()
            number_available = ''.join(
                filter(str.isdigit, raw_number_available))
        except:
            number_available = ''
    except:
        price_including_tax = ''
        universal_product_code = ''
        price_excluding_tax = ''
        number_available = ''

    try:
        div_title = soup.find(class_='col-sm-6 product_main')
        title = div_title.find("h1").get_text()
    except:
        title = ''

    product_page_url = url

    try:
        div_header_prod_desc = soup.find_all('div',
                                             id='product_description',
                                             class_='sub-header')
        prod_desc_html = div_header_prod_desc[0].next_sibling.next_sibling
        product_description = prod_desc_html.get_text()
    except:
        product_description = ''

    breadcrumb = soup.find("ul", {"class": "breadcrumb"})
    category_html = breadcrumb.find_all('a')[2]
    category_name = category_html.get_text()
    category_href = category_html['href']
    category_num = int(get_cat_num(category_href))
    numbered_category_name = f'{category_num:02d}-{category_name}'
    review_rating = num_stars(soup)

    try:
        image_path = soup.find('img')['src']
        image_path_short = re.findall("(?<=../..)[^\]]+", image_path)[0]
        image_url = base + image_path_short
    except:
        image_url = ''

    file_path = create_csv(numbered_category_name)
    row = [
        product_page_url,
        universal_product_code,
        title,
        price_including_tax,
        price_excluding_tax,
        number_available,
        product_description,
        category_name,  # category
        review_rating,
        image_url
    ]

    return [file_path, row, numbered_category_name]


def num_stars(soup):
    # finds the number of stars of a book based on the class of p tag
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


def download_book_img(numbered_category_name, book_title, image_url):
    # create a folder named after the category
    title = slugify(book_title)
    path = f"extracted data/book images/{numbered_category_name}"
    Path(path).mkdir(parents=True, exist_ok=True)
    r = requests.get(image_url, allow_redirects=True)

    open(f'{path}/{title}.jpg', 'wb').write(r.content)


def create_csv(csv_name):
    # creates a csv file if it doesn't already exist
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


def add_row(file_path, row):
    # appends a row to a csv file
    with open(file_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(row)
    f.close()


def main():
    try:
        print_logo(ascii_art)
    except:
        print("error printing logo")
    # creates a folder 'extracted data'
    Path("./extracted data/csv files").mkdir(parents=True, exist_ok=True)
    # creates a sub-folder 'book images'
    Path("./extracted data/book images").mkdir(parents=True, exist_ok=True)
    # gets the list of categories from the base
    categories_url = scrape_categories(base)
    total_books = count_books(base)
    books_scraped = 0
    # loop through the categories
    for category_url in categories_url:
        # create a csv file in the folder 'csv files' name category.csv
        category_name = get_cat_name(category_url)
        # get the category name from url
        category_num = get_cat_num(category_url)
        pages = list_category_pages(category_url)
        num_books_in_cat = get_cat_size(category_url)
        books_scraped_in_cat = 0
        print(f'🤖 Scraping category {category_name}...')
        with IncrementalBar('Progress: ', max=num_books_in_cat) as bar:
            # IncrementalBar displays the loading bar progressing
            for page in pages:
                books_on_page = list_books_urls(page)
                for book_url in books_on_page:
                    # print(f'{index}{len(books_on_page)} / books to scrape')
                    data = scrape_book_url(book_url)
                    # TODO refacto this
                    add_row(data[0], data[1])
                    download_book_img(data[2], data[1][2], data[1][9])
                    books_scraped += 1
                    bar.next()  # increment the loading bar by 1
            print(f'\n📚 {books_scraped} / {total_books} books scraped so far!')
            bar.finish()
    print(f'🥳 Scraping finished, 📚 {books_scraped} books have been scraped!')


if __name__ == "__main__":
    main()
