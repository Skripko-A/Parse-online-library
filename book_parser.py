import requests
from pathlib import Path
from bs4 import BeautifulSoup


def book_request(book_id):
    url = f'https://tululu.org/b{book_id}/'
    book_response = requests.get(url, allow_redirects=False)
    book_response.raise_for_status()
    return book_response


def check_for_redirect(response):
    if response.status_code >= 300:
        raise requests.HTTPError


def book_download_request(book_id: int):
    url = 'https://tululu.org/txt.php'
    payload = {'id': book_id}
    book_download_response = requests.get(url, params=payload, allow_redirects=False)
    book_download_response.raise_for_status()
    return book_download_response


def serialize_book(book_response, book_id):
    soup = BeautifulSoup(book_response.text, 'lxml')
    book = {'id': book_id}
    book_header = soup.find(id='content').find('h1').text.split('\xa0')
    book['title'] = book_header[0]
    book['author'] = book_header[2]
    return book


def download_book(dir_name, book_title, response, book_id):
    filename = f'{dir_name}/{book_id}. {book_title}.txt'
    with open(filename, 'wb') as file:
        file.write(response.content)
    return filename


def main():
    dir_name = Path('books')
    dir_name.mkdir(exist_ok=True)
    first_book_id = 1
    last_book_id = 10
    for book_id in range(first_book_id, last_book_id + 1):
        book_response = book_request(book_id)
        try:
            check_for_redirect(book_response)
        except requests.HTTPError:
            continue
        book = serialize_book(book_response, book_id)
        download_book(dir_name, book['title'], book_download_request(book_id), book['id'])
        print(book_id)


main()
