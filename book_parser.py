import os

import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit


def book_request(book_id):
    url = f'https://tululu.org/b{book_id}/'
    book_response = requests.get(url, allow_redirects=False)
    book_response.raise_for_status()
    print('book_request')
    return book_response


def check_for_redirect(response):
    if response.status_code >= 300:
        raise requests.HTTPError


def serialize_book(book_response, book_id, base_url):
    soup = BeautifulSoup(book_response.text, 'lxml')
    book = {'id': book_id}
    book_header = soup.find(id='content').find('h1').text.split('\xa0')
    book['title'] = book_header[0]
    book['author'] = book_header[2]
    book['img'] = urljoin(base_url, soup.find(id='content').find('img')['src'])
    book['comments'] = [book_comment.text.split(')')[1] for book_comment in soup.find_all('div', class_='texts')]

    return book


def book_download_request(book_id: int):
    url = 'https://tululu.org/txt.php'
    payload = {'id': book_id}
    book_download_response = requests.get(url, params=payload, allow_redirects=False)
    book_download_response.raise_for_status()
    print('book_download_request')
    return book_download_response


def download_book(dir_name, book_title, response, book_id):
    filename = f'{dir_name}/{book_id}. {book_title}.txt'
    with open(filename, 'wb') as file:
        file.write(response.content)
    return filename


def download_book_cover(book_img_url_path, dir_name, book_image_full_url):
    response = requests.get(book_image_full_url)
    response.raise_for_status()
    filename = os.path.join(dir_name, book_img_url_path.split('/')[2])
    with open(filename, 'wb') as file:
        file.write(response.content)
    return filename


def main():
    base_url = 'https://tululu.org'
    books_dir_name = Path('books')
    books_dir_name.mkdir(exist_ok=True)
    images_dir_name = Path('images')
    images_dir_name.mkdir(exist_ok=True)
    first_book_id = 1
    last_book_id = 10
    for book_id in range(first_book_id, last_book_id + 1):
        book_response = book_request(book_id)
        try:
            check_for_redirect(book_response)
        except requests.HTTPError:
            continue
        book = serialize_book(book_response, book_id, base_url)
        download_book(books_dir_name, book['title'], book_download_request(book_id), book['id'])
        download_book_cover(urlsplit(book['img'])[2], images_dir_name, book['img'])
        print(book)


main()
