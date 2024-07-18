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


def request_for_book(url, params: dict, log_message: str):
    """
    Выполняет HTTP-запрос к странице книги по заданному идентификатору книги.

    Функция формирует URL-адрес книги на основе идентификатора книги, выполняет
    GET-запрос к этому URL и возвращает ответ сервера. Если запрос не удается,
    функция вызывает исключение.

    Args:
        url (str): Ардес страницы для запроса
        params (dict): Параметры для запроса скачивания текста книги
        log_message (str): Текст для информационного сообщения о том, что отправлен запрос

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
    book_response = requests.get(url, allow_redirects=False, timeout=3, params=params)
    book_response.raise_for_status()
    logger.info(log_message)
    return book_response


def check_for_redirect(response, book_error: str):
    """
    Проверяет, произошел ли редирект для данного ответа.

    Если статус код ответа указывает на редирект (300-399), генерирует исключение HTTPError.

    Args:
        response (requests.Response): Объект ответа HTTP.
        book_error (str): Текст ошибки для пользователя

    Raises:
        Custom Error если по id не найдена страница книги или на странице книги не доступен файл текста книги для скачивания
    """
    if response.is_redirect:
        raise ValueError(book_error)


def extract_book_details(book_response, book_id: int) -> dict:
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

    book_header = soup.find(id='content').find('h1').text.split('\xa0')
    book = {
        'id': book_id, 'title': book_header[0],
        'author': book_header[2],
        'img': urljoin(book_response.url, soup.find(id='content').find('img')['src']),
        'comments': [book_comment.text.split(')')[1] for book_comment in soup.find_all('div', class_='texts')],
        'genres': [book_genre.text for book_genre in soup.find('span', class_='d_book').find_all('a')]
    }
    return book


def save_book_text(dir_name: Path, book_title: str, response, book_id: int) -> str:
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
    books_dir_name = Path('books')
    books_dir_name.mkdir(exist_ok=True)
    images_dir_name = Path('images')
    images_dir_name.mkdir(exist_ok=True)
    first_book_id = cli_args.start_id
    last_book_id = cli_args.end_id
    main_page_url = 'https://tululu.org/'
    for book_id in range(first_book_id, last_book_id + 1):
        while True:
            try:
                book_response = request_for_book(url=f'{main_page_url}b{book_id}/', params=None,
                                                 log_message='Запрос страницы книги')
                check_for_redirect(book_response, 'Страница книги с данным id не найдена\n')
                book = extract_book_details(book_response, book_id, book_response.url)

                book_download_response = request_for_book(url=f'{main_page_url}txt.php', params={'id': book_id},
                                                          log_message='Запрос страницы скачивания текста книги')
                check_for_redirect(book_download_response,
                                   'На странице данной книги недоступен файл текста для скачивания\n')
                save_book_text(books_dir_name, book['title'], book_download_response, book['id'])

                download_book_cover(urlsplit(book['img'])[2], images_dir_name, book['img'])

                print(f"Название: {book['title']}\nАвтор: {book['author']}\n")
                break
            except requests.ConnectionError:
                logger.error("Ошибка подключения, проверьте доступ в интернет")
                sleep(3)
            except requests.Timeout:
                logger.error('Время ожидания ответа превышено')
            except ValueError as error:
                logger.error(error)
                break
            continue


if __name__ == '__main__':
    main()
