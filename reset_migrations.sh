find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc"  -delete

pip install --upgrade --force-reinstall  Django==2.2

python manage.py makemigrations
python manage.py migrate

# python manage.py makemigrations main
# python manage.py makemigrations scheduling

# python manage.py migrate main
# python manage.py migrate scheduling

# python manage.py migrate