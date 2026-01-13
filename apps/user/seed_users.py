from apps.user.models import User


def seed_users():
    user_data = [
        {
            "email": "rafi.cse.ahmed@gmail.com",
            "full_name": "Rafi Ahmed",
            "avatar": "avatars/1.jpg",
            "password": "12345678",
            "is_staff": True,
            "is_superuser": True,
          
        },
        {
            "email": "admin@admin.com",
            "full_name": "Admin User",
            "avatar": "avatars/1.jpg",
            "password": "12345678",
            "is_staff": True,
            "is_superuser": True,
          
        },

        {
            "email": "user1@user1.com",
            "full_name": "User One",
            "avatar": "avatars/2.jpg",
            "password": "12345678",
            "is_staff": False,
            "is_superuser": False,
            "is_vendor": False,
           
        },
        {
            "email": "user2@user2.com",
            "full_name": "User Two",
            "avatar": "avatars/3.jpg",
            "password": "12345678",
            "is_staff": False,
            "is_superuser": False,
            "is_customer": True,
            
        },
        {
            "email": "user3@user3.com",
            "full_name": "User Three",
            "avatar": "avatars/4.jpg",
            "password": "12345678",
            "is_staff": False,
            "is_superuser": False,
           
        },
        {
            "email": "user4@user4.com",
            "full_name": "User Four",
            "avatar": "avatars/5.jpg",
            "password": "12345678",
            "is_staff": False,
            "is_superuser": False,
           
        }

    ]

    for user in user_data:
         User.objects.create_user(
            email=user["email"],
            full_name=user["full_name"],
            avatar=user["avatar"],
            password=user["password"],
            is_staff=user["is_staff"],
            is_superuser=user["is_superuser"],
        )

       


    print("✅ User data seeded successfully.")