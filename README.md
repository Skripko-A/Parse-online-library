# Book Parser

Макс, парсер готов. Книжки качает, обложки качает, названия книжек, авторов, 
все разборчиво, понятно.  Дедушка не запутается. Эх был бы такой сайт с API можно было бы 
столько придумать, и по жанрам искать, и по авторам.

## Оглавление
- [Требования](#требования)
- [Установка](#установка)
- [Использование](#использование)

## Требования

- Python 3.6+
- Библиотеки, указанные в `requirements.txt`

## Установка

1. **Клонируйте репозиторий:**

    ```sh
    git clone https://github.com/ваш-логин/book-downloader.git
    cd book-downloader
    ```

2. **Создайте виртуальное окружение (опционально):**

    ```sh
    python -m venv venv
    source venv/bin/activate  # для Windows: venv\Scripts\activate
    ```

3. **Установите зависимости:**

    ```sh
    pip install -r requirements.txt
    ```

## Использование

Для использования скрипта, запустите его с указанием диапазона номеров книг, которые вы хотите скачать:

```sh
python main.py -s <start_id> -e <end_id>
```

Например, чтобы скачать книги с id от 1 до 10:

```sh
python main.py -s 1 -e 10
```