"""Isolated PostgreSQL verification only; never load in an application deployment."""
from .test_settings import *  # noqa: F403
import os
DATABASES={"default":{"ENGINE":"django.db.backends.postgresql","NAME":"chat_test",
    "USER":"chat_test","PASSWORD":os.environ["LC_PG_PASSWORD"],"HOST":os.environ["LC_PG_HOST"],"PORT":"5432"}}
