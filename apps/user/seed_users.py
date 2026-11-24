from apps.user.models import StageName, User, Niche, AvailableNiche



def seed_users():
    user_data = [
        {
            "email": "rafi.cse.ahmed@gmail.com",
            "full_name": "Rafi Ahmed",
            "avatar": "avatars/1.jpg",
            "password": "12345678",
            "is_staff": True,
            "is_superuser": True,
            "term_and_condition_accepted": True,
          
        },
        {
            "email": "admin@admin.com",
            "full_name": "Admin User",
            "avatar": "avatars/1.jpg",
            "password": "12345678",
            "is_staff": True,
            "is_superuser": True,
            "term_and_condition_accepted": True,
          
        },

        {
            "email": "customer@customer.com",
            "full_name": "Customer User",
            "role": "customer",
            "avatar": "avatars/2.jpg",
            "password": "12345678",
            "is_staff": False,
            "is_superuser": False,
            "is_vendor": False,
            "term_and_condition_accepted": True,
           
        },
        {
            "email": "agency@agency.com",
            "full_name": "Agency User",
            "role": "agency",
            "avatar": "avatars/3.jpg",
            "password": "12345678",
            "is_staff": False,
            "is_superuser": False,
            "is_customer": True,
            "term_and_condition_accepted": True,
            
        },
        {
            "email": "customer1@customer.com",
            "full_name": "User Three",
            "avatar": "avatars/4.jpg",
            "password": "12345678",
            "is_staff": False,
            "is_superuser": False,
            "term_and_condition_accepted": True,
           
        },
        {
            "email": "customer2@customer.com",
            "full_name": "User Four",
            "avatar": "avatars/5.jpg",
            "password": "12345678",
            "is_staff": False,
            "is_superuser": False,
            "term_and_condition_accepted": True,
           
        }

    ]

    for user in user_data:
        if not User.objects.filter(email=user["email"]).exists():
            User.objects.create_user(
                email=user["email"],
                full_name=user["full_name"],
                avatar=user["avatar"],
                password=user["password"],
                is_staff=user["is_staff"],
                is_superuser=user["is_superuser"],
                term_and_condition_accepted=user["term_and_condition_accepted"],
                role=user.get("role", "customer"),
            )

    print("[SUCCESS] User data seeded successfully.")

def seed_customer_niches():
    niches = [
        "Instagram Influencer",
        "YouTube Creator",
        "TikTok Creator",
        "Facebook Influencer",
        "Twitter (X) Influencer",
        "LinkedIn Creator",
        "Fashion & Lifestyle Influencer",
        "Fitness & Health Influencer",
        "Tech Reviewer",
        "Gaming Streamer",
        "Musician / Artist",
        "Actor / Actress",
        "Sports Personality",
        "Content Creator",
        "Podcaster",
        "Comedian",
        "Food Blogger",
        "Travel Blogger",
        "Beauty Influencer",
        "Motivational Speaker"
    ]

    for niche in niches:
        AvailableNiche.objects.get_or_create(name=niche)

    print("[SUCCESS] Available niches seeded successfully.")


def seed_customer_stage_names():
    customer = User.objects.get(id=3)

    stage_names = [
        "Discovered",
        "Contacted",
        "Interested",
        "Profile Verified",
        "Negotiation Started",
        "Contract Signed",
        "Onboarding",
        "Campaign Assigned",
        "Content Published",
        "Campaign Completed",
        "Payment Released",
        "Active Collaboration",
        "Paused",
        "Rejected",
        "Inactive"
    ]

    for stage_name in stage_names:
        StageName.objects.get_or_create(customer = customer, name=stage_name)

    print("[SUCCESS] Social media & celebrity stage names seeded successfully.")
