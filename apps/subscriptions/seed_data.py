from apps.subscriptions.models import Feature, Package, Subscription
from django.db import connection

def seed_subscription_features():
    if Feature.objects.exists():
        print("[INFO] Subscription features already seeded.")
        return
    feature_data = [
        {'name': 'Anonymity'},
        {'name': 'Weekly Report'},
        {'name': 'Daily Report'},

        {'name': '2 Stage Names'},
        {'name': '3 Stage Names'},
        {'name': '4 Stage Names'},
        {'name': 'Unlimited Stage Names'},

        {'name': 'Weekly Scans'},
        {'name': 'Daily Scans'},

        {'name': 'Unlimited Google Delisting'},
        {'name': 'Unlimited Bing Delisting'},
        {'name': 'Unlimited Social Media Removals'},

        {'name': '50 User Submitted Requests /mo'},
        {'name': '100 User Submitted Requests /mo'},
        {'name': '200 User Submitted Requests /mo'},
        {'name': 'Unlimited User Submitted Requests /mo'},
        {'name': 'Unlimited User Submitted Requests per Month'},

        {'name': 'Basic Scan with up to 150 links removed /mo'},
        {'name': 'Basic Scan with up to 300 links removed /mo'},
        {'name': 'Advanced Scan with up to 600 links removed /mo'},
        {'name': 'Quantum Scan with unlimited links removed'},

        {'name': 'Specialized Human Searches'},
        {'name': 'Dedicated Support'},
    ]

    for feature in feature_data:
        Feature.objects.get_or_create(**feature)

    print("[SUCCESS] Features seeded successfully.")


def seed_subscription_packages():
    if Package.objects.exists():
        print("[INFO] Subscription packages already seeded.")
        return

    package_data = [

        # --------------------
        # MONTHLY PACKAGES
        # --------------------
        {
            'name': 'Starlet',
            'price': 34.99,
            'type': Package.PackageType.MONTHLY,
            'link_removal_limit_per_month':150,
            'feature_names': [
                'Anonymity',
                'Weekly Report',
                '2 Stage Names',
                'Weekly Scans',
                'Unlimited Google Delisting',
                '50 User Submitted Requests /mo',
                'Basic Scan with up to 150 links removed /mo',
            ]
        },
        {
            'name': 'Star',
            'price': 64.99,
            'type': Package.PackageType.MONTHLY,
            'link_removal_limit_per_month':300,
            'is_recommend': True,
            'feature_names': [
                'Anonymity',
                'Weekly Report',
                '3 Stage Names',
                'Weekly Scans',
                'Unlimited Google Delisting',
                'Unlimited Bing Delisting',
                '100 User Submitted Requests /mo',
                'Basic Scan with up to 300 links removed /mo',
            ]
        },
        {
            'name': 'Superstar',
            'price': 119.99,
            'type': Package.PackageType.MONTHLY,
            'link_removal_limit_per_month':600,
            'feature_names': [
                'Anonymity',
                'Daily Report',
                '4 Stage Names',
                'Daily Scans',
                'Unlimited Google Delisting',
                'Unlimited Bing Delisting',
                'Unlimited Social Media Removals',
                '200 User Submitted Requests /mo',
                'Advanced Scan with up to 600 links removed /mo',
            ]
        },
        {
            'name': 'VIP',
            'price': 229.99,
            'type': Package.PackageType.MONTHLY,
            'link_removal_limit_per_month': 340,
            'feature_names': [
                'Anonymity',
                'Daily Report',
                'Unlimited Stage Names',
                'Daily Scans',
                'Unlimited Google Delisting',
                'Unlimited Bing Delisting',
                'Unlimited Social Media Removals',
                'Unlimited User Submitted Requests /mo',
                'Quantum Scan with unlimited links removed',
                'Specialized human searches',
                'Dedicated Support',
            ]
        },

        # --------------------
        # YEARLY PACKAGES
        # --------------------
        {
            'name': 'Starlet (Yearly)',
            'price': 299.99,
            'type': Package.PackageType.YEARLY,
            'link_removal_limit_per_month':150,
            'feature_names': [
                'Anonymity',
                'Weekly Report',
                '2 Stage Names',
                'Weekly Scans',
                'Unlimited Google Delisting',
                '50 User Submitted Requests /mo',
                'Basic Scan with up to 150 links removed /mo',
            ]
        },
        {
            'name': 'Star (Yearly)',
            'price': 549.99,
            'type': Package.PackageType.YEARLY,
            'link_removal_limit_per_month':300,
            'is_recommend': True,
            'feature_names': [
                'Anonymity',
                'Weekly Report',
                '3 Stage Names',
                'Weekly Scans',
                'Unlimited Google Delisting',
                'Unlimited Bing Delisting',
                '100 User Submitted Requests /mo',
                'Basic Scan with up to 300 links removed /mo',
            ]
        },
        {
            'name': 'Superstar (Yearly)',
            'price': 999.99,
            'type': Package.PackageType.YEARLY,
            'link_removal_limit_per_month':600,
            'feature_names': [
                'Anonymity',
                'Daily Report',
                '4 Stage Names',
                'Daily Scans',
                'Unlimited Google Delisting',
                'Unlimited Bing Delisting',
                'Unlimited Social Media Removals',
                '200 User Submitted Requests /mo',
                'Advanced Scan with up to 600 links removed /mo',
            ]
        },
        {
            'name': 'VIP (Yearly)',
            'price': 1899.99,
            'type': Package.PackageType.YEARLY,
            'link_removal_limit_per_month': 340,
            'feature_names': [
                'Anonymity',
                'Daily Report',
                'Unlimited Stage Names',
                'Daily Scans',
                'Unlimited Google Delisting',
                'Unlimited Bing Delisting',
                'Unlimited Social Media Removals',
                'Unlimited User Submitted Requests /mo',
                'Quantum Scan with unlimited links removed',
                'Specialized human searches',
                'Dedicated Support',
            ]
        },

    # --------------------
    # AGENCY PACKAGES
    # --------------------
        {
            'name': 'Silver',
            'price': 900.00,
            'type': Package.PackageType.AGENCY,
            'member_limit': 10,
            'feature_names': [
                'Daily Report',
                'Unlimited Stage Names',
                'Daily Scans',
                'Unlimited Google Delisting',
                'Unlimited Bing Delisting',
                'Unlimited Social Media Removals',
                'Unlimited User Submitted Requests per Month',
                'Quantum Scan with Unlimited Links Removed',
                'Specialized Human Searches',
                'Dedicated Support',
            ]
        },
        {
            'name': 'Gold',
            'price': 1700.00,
            'type': Package.PackageType.AGENCY,
            'member_limit': 20,
            'is_recommend': True,
            'feature_names': [
                'Daily Report',
                'Unlimited Stage Names',
                'Daily Scans',
                'Unlimited Google Delisting',
                'Unlimited Bing Delisting',
                'Unlimited Social Media Removals',
                'Unlimited User Submitted Requests per Month',
                'Quantum Scan with Unlimited Links Removed',
                'Specialized Human Searches',
                'Dedicated Support',
            ]
        },
        {
            'name': 'Platinum',
            'price': 2400.00,
            'type': Package.PackageType.AGENCY,
            'member_limit': 30,
            'feature_names': [
                'Daily Report',
                'Unlimited Stage Names',
                'Daily Scans',
                'Unlimited Google Delisting',
                'Unlimited Bing Delisting',
                'Unlimited Social Media Removals',
                'Unlimited User Submitted Requests per Month',
                'Quantum Scan with Unlimited Links Removed',
                'Specialized Human Searches',
                'Dedicated Support',
            ]
        },
        {
            'name': 'Diamond',
            'price': 3000.00,
            'type': Package.PackageType.AGENCY,
            'member_limit': 50,
            'feature_names': [
                'Daily Report',
                'Unlimited Stage Names',
                'Daily Scans',
                'Unlimited Google Delisting',
                'Unlimited Bing Delisting',
                'Unlimited Social Media Removals',
                'Unlimited User Submitted Requests per Month',
                'Quantum Scan with Unlimited Links Removed',
                'Specialized Human Searches',
                'Dedicated Support',
            ]
        },
    ]

    for package_info in package_data:
        feature_names = package_info.pop('feature_names', [])

        package = Package.objects.create(**package_info)

        features = Feature.objects.filter(name__in=feature_names)
        package.features.set(features)

    print("[SUCCESS] Packages seeded successfully.")


def seed_subscription():
    if Subscription.objects.exists():
        print("[INFO] Subscriptions already seeded.")
        return

    subscriptions_data = [
        {
            'user_id': 1,
            'package_name': 'Star',
            'status': 'active',
            'start_date': '2024-01-01T00:00:00Z',
            'end_date': '2028-02-01T00:00:00Z',
        },
        {
            'user_id': 2,
            'package_name': 'Superstar',
            'status': 'active',
            'start_date': '2023-12-15T00:00:00Z',
            'end_date': '2028-02-15T00:00:00Z',
        },
        {
            'user_id': 4,
            'package_name': 'Silver',
            'status': 'active',
            'start_date': '2023-12-01T00:00:00Z',
            'end_date': '2028-01-01T00:00:00Z',
        },
    ]

    for sub_data in subscriptions_data:
        package = Package.objects.get(name=sub_data.pop('package_name'))
        Subscription.objects.create(package=package, **sub_data)

    print("[SUCCESS] Subscriptions seeded successfully.")