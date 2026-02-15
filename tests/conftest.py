import os

import django
import pytest


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


@pytest.fixture
def client(db):  # noqa: A001
    from django.test import Client as DjangoClient

    return DjangoClient()

