## Setup
- install postgrey sql v11.1
- install python v2.7.x
- setup [python virtual environment](https://uoa-eresearch.github.io/eresearch-cookbook/recipe/2014/11/26/python-virtual-env/)
- install python dependencies with pip install -r requirement.txt
- create workflow_platform/settings/settings_local.py
- **settings_local.py** content
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '<db_name>',
        'USER': '<db_user>',
        'PASSWORD': '<db_user_password>',
        'HOST': '<db_host>',
        'PORT': '<db_port>',
    }
}
```
- Postgresql need to install citext plugin with following command
    > CREATE EXTENSION citext;
- apply migrations with 
    > python manage.py migrate
- Yeeeehh, now you can fire your app with 
    > python manage.py runserver
 