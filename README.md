# Workflow Platform

## System Requirenment
- PostgreySQL [v11.1](https://www.postgresql.org/download/)
- Python [v2.7.x](https://www.python.org/download/releases/2.7/)

## Setup Instruction
- Setup [python virtual environment](https://virtualenvwrapper.readthedocs.io/en/latest/)
- Install project dependencies
```
pip install -r requirements.txt
```
- Create local settings by replacing placeholders from settings/settings_local.py.template and remove suffix .template
- Postgresql need to install citext plugin with following command
```
CREATE EXTENSION citext;
```
- Apply migrations with
```
python manage.py migrate
```
- Now start celery worker
```
celery -A workflow_platform worker -l info
```
- Now you can fire your app with
```
python manage.py runserver
```
**Server will start by default at [http://localhost:8000](http://localhost:8000/api/docs)**
- Swagger only show endpoint accessable to user only.
