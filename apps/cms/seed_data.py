from apps.cms.models import FAQ, AmongOurCustomer, HeroRadarIcon, HeroSection, HowItWorks, IdentityTracking, Page, Testimonial

def seed_page():
    if Page.objects.exists():
        print("[INFO] Pages already seeded.")
        return
    pages = [
        {
            "title": "Privacy Policy",
            "slug": "privacy-policy",
            "content": "This Privacy Policy explains how we collect, use, and protect your personal data when you use our website and services.",
            "type": "privacy_policy",
            "status": True
        },
        {
            "title": "Terms and Conditions",
            "slug": "terms-and-conditions",
            "content": "These Terms and Conditions govern your use of our website and services. By accessing the site, you agree to comply with these rules.",
            "type": "terms_and_conditions",
            "status": True
        },
        {
            "title": "Cookie Policy",
            "slug": "cookie-policy",
            "content": "Our website uses cookies to enhance user experience. This policy explains what cookies we use and how you can manage them.",
            "type": "cookie_policy",
            "status": True
        },
        {
            "title": "Imprint",
            "slug": "imprint",
            "content": "This Imprint provides legal information about our company, including address, contact details, and responsible representatives.",
            "type": "imprint",
            "status": True
        }
    ]
    for page in pages:
        Page.objects.create(**page)
    print("[SUCCESS] Pages seeded successfully.")


def seed_faq():
    if FAQ.objects.exists():
        print("[INFO] FAQs already seeded.")
        return
    faqs = [
        {
            "question": "How can I create an account?",
            "answer": "You can create an account by clicking the 'Sign Up' button and filling out the registration form.",
            "status": True
        },
        {
            "question": "How do I reset my password?",
            "answer": "Click on 'Forgot Password' on the login page, then follow the instructions to reset your password.",
            "status": True
        },
        {
            "question": "Can I change my email address?",
            "answer": "Yes, you can update your email in your profile settings under 'Account Information'.",
            "status": True
        },
        {
            "question": "How do I contact support?",
            "answer": "You can reach our support team via the 'Contact Us' page or by emailing support@example.com.",
            "status": True
        },
        {
            "question": "Is my personal information safe?",
            "answer": "Yes, we use industry-standard security measures to protect your data.",
            "status": True
        }
    ]

    for faq in faqs:
        FAQ.objects.create(**faq)

    print("[SUCCESS] FAQs seeded successfully.")


def seed_hero_section():
    if HeroSection.objects.exists():
        print("[INFO] Hero sections already seeded.")
        return
    hero_sections = [
        {
            "title": "Protect your images & videos automatically.",
            "subtitle": "An AI platform that detects and removes unauthorized media online, protecting your creative work around the clock with smart automation."
        }
    ]

    for hero_section in hero_sections:
        HeroSection.objects.create(**hero_section)

    print("[SUCCESS] Hero sections seeded successfully.")

    
def seed_hero_radar_icon():
    if HeroRadarIcon.objects.exists():
        print("[INFO] Hero radar icons already seeded.")
        return
    hero_radar_icons = [
       {'icon': 'cms/Radar/1.png'},
       {'icon': 'cms/Radar/2.png'},
       {'icon': 'cms/Radar/3.png'},
       {'icon': 'cms/Radar/4.png'},
       {'icon': 'cms/Radar/5.png'},
       {'icon': 'cms/Radar/6.png'},
       {'icon': 'cms/Radar/7.png'},
       {'icon': 'cms/Radar/8.png'},
       {'icon': 'cms/Radar/9.png'},
       {'icon': 'cms/Radar/10.png'},
       {'icon': 'cms/Radar/11.png'},
       {'icon': 'cms/Radar/6.png'},
    ]

    for hero_radar_icon in hero_radar_icons:
        HeroRadarIcon.objects.create(**hero_radar_icon)

    print("[SUCCESS] Hero radar icons seeded successfully.")
    
    
def seed_represent_platform():
    from apps.cms.models import RepresentPlatform
    if RepresentPlatform.objects.exists():
        print("[INFO] Represent platforms already seeded.")
        return

    platforms = [
        {
            "name": "Chaturtle",
            "icon": "cms/platform/1.png",
            "status": True
        },
        {
            "name": "Fancy",
            "icon": "cms/platform/2.svg",
            "status": True
        },
        {
            "name": "Fanvue",
            "icon": "cms/platform/3.png",
            "status": True
        },
        {
            "name": "Manivids",
            "icon": "cms/platform/4.png",
            "status": True
        },
        {
            "name": "OnlyFans",
            "icon": "cms/platform/5.svg",
            "status": True
        }
    ]

    for platform in platforms:
        RepresentPlatform.objects.create(**platform)

    print("[SUCCESS] Represent platforms seeded successfully.")


def seed_among_our_customers():
    if AmongOurCustomer.objects.exists():
        print("[INFO] Among our customers already seeded.")
        return

    customers = [
        {
            "name": "Sarah Johnson",
            "profile_pic": "cms/customers/1.png",
            "social_media_icon": "cms/customers/bchaturbate.png",
            "followers_count": 12.5,
            "status": True
        },
        {
            "name": "Mike Thompson",
            "profile_pic": "cms/customers/2.png",
            "social_media_icon": "cms/customers/Facebook.png",
            "followers_count": 89.0,
            "status": True
        },
        {
            "name": "Emily Chen",
            "profile_pic": "cms/customers/3.png",
            "social_media_icon": "cms/customers/hamster.png",
            "followers_count": 15,
            "status": True
        },
        {
            "name": "Alex Martinez",
            "profile_pic": "cms/customers/4.png",
            "social_media_icon": "cms/customers/Facebook.png",
            "followers_count": 2.5,
            "status": True
        },
        {
            "name": "Jessica Williams",
            "profile_pic": "cms/customers/5.png",
            "social_media_icon": "cms/customers/Instagram.png",
            "followers_count": 45.3,
            "status": True
        },
        {
            "name": "David Brown",
            "profile_pic": "cms/customers/6.png",
            "social_media_icon": "cms/customers/por.png",
            "followers_count": 8.7,
            "status": True
        }
    ]

    for customer in customers:
        AmongOurCustomer.objects.create(**customer)

    print("[SUCCESS] Among our customers seeded successfully.")
    
    
def seed_testimonials():
    if Testimonial.objects.exists():
        print("[INFO] Testimonials already seeded.")
        return
    
    testimonials = [
        {
            "name": "Laura Smith",
            "profession": "Content Creator",
            "profile_pic": "cms/testimonials/1.png",
            "rating": 5,
            "platform": "cms/testimonials/chaturbate.png",
            "review_title": "Excellent Service!",
            "review": "This platform has transformed the way I protect my content. The AI detection is incredibly accurate and efficient.",
        },
        {
            "name": "James Wilson",
            "profession": "Photographer",
            "profile_pic": "cms/testimonials/2.png",
            "rating": 4,
            "platform": "cms/testimonials/fanvue.png",
            "review_title": "Very Reliable",
            "review": "I feel much more secure knowing that my images are being monitored and protected around the clock.",
        },
        {
            "name": "Megan Lee",
            "profession": "Videographer",
            "profile_pic": "cms/testimonials/3.png",
            "rating": 5,
            "platform": "cms/testimonials/ManyVids.png",
            "review_title": "Highly Recommend!",
            "review": "The automation features save me so much time. I can focus on creating while the platform handles the rest.",
        },
        {
            "name": "David Kim",
            "profession": "Blogger",
            "profile_pic": "cms/testimonials/4.png",
            "rating": 4,
            "platform": "cms/testimonials/Onlyfans.svg",
            "review_title": "Great Support",
            "review": "The customer support team is responsive and helpful. They assisted me with setting up my account quickly.",
        },
        {
            "name": "Sophia Garcia",
            "profession": "Artist",
            "profile_pic": "cms/testimonials/5.png",
            "rating": 5,
            "platform": "cms/testimonials/fanvue.png",
            "review_title": "Fantastic Experience",
            "review": "Using this platform has been a game-changer for my online presence. I feel confident sharing my work now.",
        },
        {
            "name": "Michael Johnson",
            "profession": "Musician",
            "profile_pic": "cms/testimonials/6.png",
            "rating": 5,
            "platform": "cms/testimonials/ManyVids.png",
            "review_title": "Top Notch Protection",
            "review": "The AI technology is impressive. It quickly identifies unauthorized use of my music and takes action.",
        },
        {
            "name": "Olivia Brown",
            "profession": "Influencer",
            "profile_pic": "cms/testimonials/7.png",
            "rating": 4,
            "platform": "cms/testimonials/fanvue.png",
            "review_title": "Very Effective",
            "review": "I've seen a significant decrease in content theft since using this service. It's definitely worth it.",
        },
        {
            "name": "Daniel Davis",
            "profession": "Writer",
            "profile_pic": "cms/testimonials/8.png",
            "rating": 5,
            "platform": "cms/testimonials/ManyVids.png",
            "review_title": "Impressive Results",
            "review": "The platform's ability to detect and remove unauthorized content is outstanding. Highly effective!",
        }
    ]

    for testimonial in testimonials:
        Testimonial.objects.create(**testimonial)

    print("[SUCCESS] Testimonials seeded successfully.")


def seed_how_it_works():
    if HowItWorks.objects.exists():
        print("[INFO] How it works already seeded.")
        return

    how_it_works = [
        {
            "question": "Create & Optimize a free account",
            "answer": "Sign up for a free DIY account. You can specify your niches and all of your usernames to make sure the free scan finds as many leaks as possible.",
            "status": True
        },
        {
            "question": "Explore where your leaks appear",
            "answer": "Our platform helps you quickly identify where your content or data is leaking online. With detailed scanning tools, you can pinpoint the exact sources of leaks, making it easy to take action before they spread further.",
            "status": True
        },
        {
            "question": "Remove leaks by yourself or automatically",
            "answer": "You have full control over leak removal. Choose to handle it manually with our step-by-step tools, or let our system automatically remove unauthorized content for you, saving time and ensuring faster protection.",
            "status": True
        },
        {
            "question": "Track progress & automatic scans",
            "answer": "Stay updated on your leak protection efforts with real-time tracking. Our automatic scans continuously monitor the web for new leaks, and you can track removal success, statistics, and overall progress from your dashboard.",
            "status": True
        },
    ]

    for how_it_work in how_it_works:
        HowItWorks.objects.create(**how_it_work)

    print("[SUCCESS] How it works seeded successfully.")


def seed_identity_tracking():
    if IdentityTracking.objects.exists():
        print("[INFO] Identity tracking already seeded.")
        return

    identity_tracking = [
        {
            "title": "Searching through all of your stage names is how I found you.",
            "short_description": "To ensure full coverage, our AI searches for unauthorized content using all of your stage names.",
            "image": "cms/identity_tracking/1.png",
        },
    ]

    for identity_tracking in identity_tracking:
        IdentityTracking.objects.create(**identity_tracking)

    print("[SUCCESS] Identity tracking seeded successfully.")


def seed_our_metrics():
    from apps.cms.models import OurMetrics
    if not OurMetrics.objects.exists():
        OurMetrics.objects.create(
            section_title="Our Metrics",
            header_title="Numbers Matters",
            web_search="+55M",
            web_search_label="Web search",
            content_creators="+1M",
            content_creators_label="Content Creators",
            leaks_found="+55M",
            leaks_found_label="Leaks found",
            recovered="+55M",
            recovered_label="Recovered",
            success_score="+100%",
            success_score_label="Success Score",
            status=True
        )
        print("[SUCCESS] Our Metrics seeded successfully.")
    else:
        print("[INFO] Our Metrics already exists.")