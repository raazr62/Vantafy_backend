import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

with connection.cursor() as cursor:
    # Get table info. For SQLite it's PRAGMA table_info, for Postgres it's strictly different.
    # But django introspection is easier.
    introspection = connection.introspection
    table_name = 'user_user'
    try:
        columns = [col.name for col in introspection.get_table_description(cursor, table_name)]
        print(f"Columns in {table_name}: {columns}")
        if 'full_name' in columns:
            print("full_name column EXISTS.")
        else:
            print("full_name column is MISSING.")
            
        if 'avatar' in columns:
            print("avatar column EXISTS.")
        else:
            print("avatar column is MISSING.")
    except Exception as e:
        print(f"Error: {e}")
