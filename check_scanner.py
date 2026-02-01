import os
import django
import sys

# Setup Django environment
sys.path.append(r'c:\Users\Rafi\django_projects\fixing\mediamixer_django')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.scanner.models import CustomerScanProcessing, CustomerScanResult, AgencyMemberScanProcessing, AgencyMemberScanResult
from apps.user.models import User, AgencyMemberList
from django.conf import settings

def test_scanner_logic():
    print("Testing Scanner Models Logic...")
    
    # Check if we can get result model
    p = CustomerScanProcessing()
    res_model = p.get_result_model()
    print(f"CustomerScanProcessing Result Model: {res_model.__name__}")
    assert res_model == CustomerScanResult
    
    # Verify search_name property existence
    print("Checking search_name property...")
    assert hasattr(CustomerScanProcessing, 'search_name')
    assert hasattr(AgencyMemberScanProcessing, 'search_name')

    print("Scan Logic verification passed.")

if __name__ == "__main__":
    test_scanner_logic()
