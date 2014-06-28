.PHONY: example

example:
	DJANGO_SETTINGS_MODULE=example.settings \
		django-admin.py runserver
