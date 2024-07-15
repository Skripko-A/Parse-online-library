import os
from time import sleep

import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit
import argparse
import logging


logger = logging.getLogger('logger')


def set_cli_args():
    """
    Создает и настраивает парсер командной строки для задания диапазона скачиваемых книг.

    Args:
        - start_id (-s или --start_id): нижняя граница диапазона скачиваемых книг (натуральное число).
        - end_id (-e или --end_id): верхняя граница диапазона скачиваемых книг (натуральное число).

    Returns:
        argparse.Namespace: Объект с разобранными аргументами командной строки.

    Пример:
        >>> args = set_cli_args()
        >>> args.start_id
        1
        >>> args.end_id
        10

    Исключения:
        SystemExit: Возникает при ошибке разбора аргументов командной строки.
    """
    parser = argparse.ArgumentParser(
        description='Укажите диапазон номеров (id) книг для скачивания.'
    )
    parser.add_argument('-s', '--start_id', type=int, required=True,
                        help='нижняя граница диапазона скачиваемых книг (натуральное число)')
    parser.add_argument('-e', '--end_id', type=int, required=True,
                        help='верхняя граница диапазона скачиваемых книг (натуральное число).')
    return parser


def request_for_book(book_id: int):
    """
    Выполняет HTTP-запрос к странице книги по заданному идентификатору книги.

    Функция формирует URL-адрес книги на основе идентификатора книги, выполняет
    GET-запрос к этому URL и возвращает ответ сервера. Если запрос не удается,
    функция вызывает исключение.

    Args:
        book_id (int): Идентификатор книги.

    Returns:
        requests.Response: Ответ сервера на HTTP-запрос.

    Raises:
        requests.exceptions.HTTPError: Если запрос возвращает код ошибки HTTP.
        requests.exceptions.RequestException: В случае других ошибок запроса.

    Пример:
        >>> response = request_for_book(1)
        >>> response.status_code
        200
    """
    url = f'https://tululu.org/b{book_id}/'
    book_response = requests.get(url, allow_redirects=False, timeout=3)
    book_response.raise_for_status()
    logger.info(f'Запрос страницы книги {book_id}')
    return book_response


def check_for_redirect(response):
    """
    Проверяет, произошел ли редирект для данного ответа.

    Если статус код ответа указывает на редирект (300-399), генерирует исключение HTTPError.

    Args:
        response (requests.Response): Объект ответа HTTP.

    Raises:
        requests.HTTPError: Если статус код ответа указывает на редирект.
    """
    if 300 <= response.status_code < 400:
        raise requests.HTTPError


def serialize_book(book_response, book_id: int, base_url: str) -> dict:
    """
    Собирает данные о книге из HTML-ответа в словарь.

    Args:
        book_response (requests.Response): HTTP-ответ с данными о книге.
        book_id (int): Идентификатор книги.
        base_url (str): Базовый URL для формирования полного пути к изображению.

    Returns:
        dict: Словарь с данными о книге.
    """
    soup = BeautifulSoup(book_response.text, 'lxml')
    book = {'id': book_id}
    book_header = soup.find(id='content').find('h1').text.split('\xa0')
    book['title'] = book_header[0]
    book['author'] = book_header[2]
    book['img'] = urljoin(base_url, soup.find(id='content').find('img')['src'])
    book['comments'] = [book_comment.text.split(')')[1] for book_comment in soup.find_all('div', class_='texts')]
    book['genres'] = [book_genre.text for book_genre in soup.find('span', class_='d_book').find_all('a')]
    return book


def book_download_request(book_id: int):
    """
    Отправляет запрос на скачивание книги по её идентификатору и возвращает HTTP-ответ.

    Args:
        book_id (int): Идентификатор книги.

    Returns:
        requests.Response: HTTP-ответ на запрос скачивания книги.

    Raises:
        requests.exceptions.RequestException: Если запрос завершился неудачно.
    """
    url = 'https://tululu.org/txt.php'
    payload = {'id': book_id}
    book_download_response = requests.get(url, params=payload, allow_redirects=False, timeout=3)
    book_download_response.raise_for_status()
    logger.info(f'Загрузка книги {book_id}')
    return book_download_response


def download_book(dir_name: Path, book_title: str, response, book_id: int) -> str:
    """
    Сохраняет содержимое HTTP-ответа в файл.

    Args:
        dir_name (str): Директория для сохранения файла.
        book_title (str): Название книги.
        response (requests.Response): HTTP-ответ с содержимым книги.
        book_id (int): Идентификатор книги.

    Returns:
        str: Полный путь к сохраненному файлу.

    Raises:
        OSError: Если произошла ошибка при записи файла.
    """
    filename = f'{dir_name}/{book_id}. {book_title}.txt'
    with open(filename, 'wb') as file:
        file.write(response.content)
    return filename


def download_book_cover(book_img_url_path: str, dir_name: Path, book_image_full_url: str) -> str:
    """
    Загружает изображение обложки книги и сохраняет его в указанной директории.

    Args:
        book_img_url_path (str): Относительный путь к изображению обложки книги.
        dir_name (str): Директория для сохранения изображения.
        book_image_full_url (str): Полный URL изображения обложки книги.

    Returns:
        str: Полный путь к сохраненному файлу.

    Raises:
        requests.HTTPError: Если запрос на получение изображения завершился с ошибкой.
        OSError: Если произошла ошибка при записи файла.
    """
    response = requests.get(book_image_full_url, timeout=3)
    response.raise_for_status()
    filename = os.path.join(dir_name, book_img_url_path.split('/')[2])
    with open(filename, 'wb') as file:
        file.write(response.content)
    return filename


def main():
    """
    Основная функция программы для скачивания книг и их обложек с сайта tululu.org.

    Функция создает необходимые директории, запрашивает информацию о книгах и скачивает их
    вместе с обложками в указанные директории.
    """
    logging.basicConfig(level=logging.ERROR)
    parser = set_cli_args()
    cli_args = parser.parse_args()
    base_url = 'https://tululu.org'
    books_dir_name = Path('books')
    books_dir_name.mkdir(exist_ok=True)
    images_dir_name = Path('images')
    images_dir_name.mkdir(exist_ok=True)
    first_book_id = cli_args.start_id
    last_book_id = cli_args.end_id
    for book_id in range(first_book_id, last_book_id + 1):
        while True:
            try:
                book_response = request_for_book(book_id)
                check_for_redirect(book_response)
                book = serialize_book(book_response, book_id, base_url)
                download_book(books_dir_name, book['title'], book_download_request(book_id), book['id'])
                download_book_cover(urlsplit(book['img'])[2], images_dir_name, book['img'])
                print(f"Название: {book['title']}\nАвтор: {book['author']}\n")
                break
            except requests.ConnectionError:
                logger.error("Ошибка подключения, проверьте доступ в интернет")
                sleep(3)
            except requests.Timeout:
                logger.error('Время ожидания ответа превышено')
            except requests.HTTPError:
                logger.error("Страница с книгой не найдена, проверьте URL запроса, id-книги, "
                             "возможно книги с таким id на сайте больше нет\n")
                break
            continue


if __name__ == '__main__':
    main()
