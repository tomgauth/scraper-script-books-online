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


def get_soup(url):
    # takes a page url and returns the page html
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)


def print_logo(ascii_art):
    with open(ascii_art, 'r', encoding='UTF-8') as f:
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
    categories = [base + '/' + n['href'] for n in category_paths]
    categories.remove(
        'http://books.toscrape.com/catalogue/category/books_1/index.html')
    return categories


def count_books(base):
    soup = get_soup(base)
    num_books_txt = soup.form.div.next_sibling.next_sibling.get_text()
    num_books_total = int(num_books_txt)
    return num_books_total


def get_cat_name_from_url(category_url):
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
    soup = get_soup(category_url)
    num_books_txt = soup.form.div.next_sibling.next_sibling.get_text()
    num_books_in_cat = int(num_books_txt)
    return num_books_in_cat


def list_category_pages(category_url):
    # takes the 1st page of the category
    # returns a list of urls of all the pages of the category
    response = requests.get(base)
    soup = get_soup(category_url)
    raw_html_books = soup.find_all('article', class_='product_pod')
    page_urls = []
    if len(raw_html_books) != 20:
        # if the page 1 shows more than 20 books, try to get next page
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


def get_table_values(soup):
    values = {}
    try:
        table = soup.find_all('table', class_='table table-striped')[0]
        try:
            values['price_including_tax'] = table.find_all('td')[3].get_text()
        except IndexError:
            print('\n price_including_tax not found')
        try:
            values['universal_product_code'] = table.find_all('td')[
                0].get_text()
        except IndexError:
            print('\n universal_product_code not found')
        try:
            values['price_excluding_tax'] = table.find_all('td')[2].get_text()
        except IndexError:
            print('\n price_excluding_tax not found')
        try:
            raw_number_available = table.find_all('td')[5].get_text()
            values['number_available'] = ''.join(
                filter(str.isdigit, raw_number_available))
        except IndexError:
            print('\n number_available not found')
    except IndexError:
        print('\n table not found')
    return values


def get_title(soup):
    try:
        product_main = soup.find(class_='product_main')
        title = product_main.find("h1").get_text()
        return title
    except IndexError:
        print('\n Title not found')


def get_prod_description(soup):
    try:
        div_header_prod_desc = soup.find('div',
                                         id='product_description',
                                         class_='sub-header')
        prod_desc_html = div_header_prod_desc.next_sibling.next_sibling
        product_description = prod_desc_html.get_text()
        return product_description
    except AttributeError:
        print('product_description not found')


def get_cat_name_soup(soup):
    try:
        breadcrumb = soup.find("ul", {"class": "breadcrumb"})
        category_html = breadcrumb.find_all('a')[2]
        category_name = category_html.get_text()
        category_href = category_html['href']
        category_num = int(get_cat_num(category_href))
        numbered_category_name = f"{category_num:02d}-{category_name}"
        return [category_name, numbered_category_name]
    except IndexError:
        print('\n category_name not found')


def get_img_url(soup):
    try:
        image_path = soup.find('img')['src']
        image_path_short = re.findall("(?<=../..)[^\]]+", image_path)[0]
        image_url = base + image_path_short
        return image_url
    except:
        print('\n image_url not found')


def scrape_book_url(url):
    # takes the url of the book page and
    # returns a dict containing: file_path, row values, numbered_category_name
    soup = get_soup(url)

    row = {
        'product_page_url': '',
        'universal_product_code': '',
        'title': '',
        'price_including_tax': '',
        'price_excluding_tax': '',
        'number_available': '',
        'product_description': '',
        'category_name': '',
        'review_rating': '',
        'image_url': '',
        'numbered_category_name': ''
    }

    table_values = get_table_values(soup)
    # gets the values: price_including_tax, universal_product_code,
    # price_excluding_tax and number_available
    row.update(table_values)
    row['product_page_url'] = url
    row['title'] = get_title(soup)
    row['product_description'] = get_prod_description(soup)
    row['category_name'] = get_cat_name_soup(soup)[0]
    row['review_rating'] = num_stars(soup)
    row['image_url'] = get_img_url(soup)
    row['numbered_category_name'] = get_cat_name_soup(soup)[1]

    return row


def num_stars(soup):
    # finds the number of stars of a book using the product_main div
    ratings = {
        'One':  1,
        'Two':  2,
        'Three':  3,
        'Four': 4,
        'Five': 5
    }
    try:
        product_main = soup.find(class_='product_main')
        rating_html = product_main.find('p', 'star-rating')
        rating_txt = rating_html['class'][1]
        return ratings.get(rating_txt, '')
    except IndexError:
        print(f'\n image_url not found')


def download_book_img(numbered_category_name, book_title, image_url):
    # create a folder named after the category
    title = slugify(book_title)
    path = f"extracted data/book images/{numbered_category_name}"
    Path(path).mkdir(parents=True, exist_ok=True)
    r = requests.get(image_url, allow_redirects=True)

    open(f'{path}/{title}.jpg', 'wb').write(r.content)


def create_csv(rows):  # create_csv(csv_name, rows)
    # creates a csv file if it doesn't already exist
    # 'numbered_category_name': numbered_category_name
    csv_name = rows[0]['numbered_category_name']
    [row.pop('numbered_category_name') for row in rows]  # removes this column
    path = f'./extracted data/csv files/{csv_name}.csv'
    p = Path(path)
    with open(path, 'a', newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(rows[0])
        for row in rows:
            writer.writerow(row.values())
    f.close()


def main():
    try:
        print_logo(ascii_art)
    except UnicodeDecodeError as error:
        print("Error displaying logo: " + error)
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
        rows = []
        # create a csv file in the folder 'csv files' name category.csv
        # get category name from url
        category_name = get_cat_name_from_url(category_url)
        pages = list_category_pages(category_url)  # list of urls of pages
        num_books_in_cat = get_cat_size(
            category_url)  # num of books in category
        print(f'🤖 Scraping category {category_name}...')
        with IncrementalBar('Progress: ', max=num_books_in_cat) as bar:
            # IncrementalBar displays the loading bar progressing
            for page in pages:
                books_on_page = list_books_urls(page)
                for book_url in books_on_page:
                    row = scrape_book_url(book_url)
                    download_book_img(row['numbered_category_name'],
                                      row['title'],
                                      row['image_url'])
                    rows.append(row)
                    books_scraped += 1
                    bar.next()  # increment the loading bar by 1
        create_csv(rows)
        print(f'\n📚 {books_scraped} / {total_books} books scraped so far!')
        bar.finish()
    print(f'🥳 Scraping finished, 📚 {books_scraped} books have been scraped!')


if __name__ == "__main__":
    main()
