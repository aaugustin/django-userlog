.PHONY: example realtime test coverage flake8

example:
	DJANGO_SETTINGS_MODULE=userlog.example_settings \
		django-admin.py runserver

realtime:
	DJANGO_SETTINGS_MODULE=userlog.example_settings \
		python -m userlog.realtime

test:
	DJANGO_SETTINGS_MODULE=userlog.test_settings \
		django-admin.py test --liveserver=localhost:8040 userlog

coverage:
	coverage erase
	DJANGO_SETTINGS_MODULE=userlog.test_settings \
		coverage run --branch --source=userlog `which django-admin.py` test --liveserver=localhost:8040 userlog
	coverage html

flake8:
	flake8 userlog
