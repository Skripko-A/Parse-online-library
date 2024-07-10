import requests
from pathlib import Path


def download_books(book_id: int, books_amount: int, dir_name, url):
    while book_id <= books_amount:
        response = requests.get(f'{url}{book_id}')
        response.raise_for_status()

        filename = f'{dir_name}/book_{book_id}.txt'
        print(filename)
        with open(filename, 'wb') as file:
            file.write(response.content)
        book_id += 1


if __name__ == '__main__':
    dir_name = Path('books')
    dir_name.mkdir(exist_ok=True)

    book_id = 1
    books_amount = 10
    url = 'https://tululu.org/txt.php?id='
    download_books(book_id, books_amount, dir_name, url)
