
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()
from django.urls import reverse
try:
    print('URL:', reverse('admin:scanner_unauthorizedwebsiteandemail_changelist'))
except Exception as e:
    print('Error:', e)

