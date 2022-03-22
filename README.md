
Сервер документов Python Django на базе OnlyOffice.

Для работы необходимо установить OnlyOffice DocServer и прописать его адрес в config.py.

За основу взят оригинальный пример https://api.onlyoffice.com/editors/example/python 

Добавлена авторизация, но работает чисто формально на главной странице и странице редактора.
Зная статичный адрес или название файла можно без проблем его скачать.

Нормальная работа с файлами возможна только созданными на главной странице. Переименование пока не реализовано. 
Если файлы загружать, то они не будут отображаться на главной странице.

Возможно для кого-то пригодится. 

Логин: admin 
Пароль: yqZapmZ7

Сервер сделан на Django. 
Чтобы запустить необходимо:
1. Открыть папку в консоли 
2. pipenv install django 
3. pipenv shell
4. Прописать адрес OnlyOffice DocServer в config.py DOC_SERV_SITE_URL = 'http://сюда вписать URL сервера/'
5. pip install requests==2.25.0
6. pip install pyjwt==1.7.1
7. pip install python-magic
8. python manage.py runserver 0.0.0.0:8000
