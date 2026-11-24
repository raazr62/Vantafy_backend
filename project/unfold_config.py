from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _


from functools import lru_cache


@lru_cache(maxsize=1)
def get_about_system():
    from apps.system_setting.models import AboutSystem

    return AboutSystem.objects.first()


from django.utils.safestring import mark_safe


def get_system_color():
    try:
        from apps.system_setting.models import SystemColor
        color = SystemColor.objects.filter(is_active=True).first()
        if color and color.code:
            return color.code.strip()
    except Exception:
        pass
    return "#FFA500"  # Default fallback system color (orange/yellow)


def hex_to_rgb(hex_code):
    hex_code = hex_code.lstrip('#')
    if len(hex_code) == 3:
        hex_code = ''.join([c*2 for c in hex_code])
    try:
        return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        return (255, 165, 0)


def get_custom_unfold_css(request=None):
    color_hex = get_system_color()
    r, g, b = hex_to_rgb(color_hex)
    rgb_str = f"{r} {g} {b}"
    return mark_safe(f"""
        <style>
            :root, html, html.dark, body, .dark {{
                --system-color: {color_hex};
                --color-primary-50: {rgb_str};
                --color-primary-100: {rgb_str};
                --color-primary-200: {rgb_str};
                --color-primary-300: {rgb_str};
                --color-primary-400: {rgb_str};
                --color-primary-500: {rgb_str};
                --color-primary-600: {rgb_str};
                --color-primary-700: {rgb_str};
                --color-primary-800: {rgb_str};
                --color-primary-900: {rgb_str};
                --color-primary-950: {rgb_str};
            }}

            /* Primary buttons & active tabs in custom admin pages */
            .scan-btn-primary,
            .tab-btn-active {{
                background-color: {color_hex} !important;
                color: #ffffff !important;
            }}

            .scan-btn-primary:hover {{
                background-color: {color_hex} !important;
                filter: brightness(0.9) !important;
                opacity: 0.95 !important;
                color: #ffffff !important;
            }}

            /* Unfold Left Sidebar Navigation (#nav-sidebar-inner) - Light & Dark Mode Overrides */
            #nav-sidebar-inner a[class*="text-primary"],
            #nav-sidebar-inner a[class*="hover:text-primary"],
            #nav-sidebar-inner a.text-primary-600,
            #nav-sidebar-inner a.text-primary-500,
            .dark #nav-sidebar-inner a[class*="text-primary"],
            .dark #nav-sidebar-inner a[class*="hover:text-primary"],
            .dark #nav-sidebar-inner a[class*="dark:text-primary"],
            .dark #nav-sidebar-inner a[class*="dark:hover:text-primary"] {{
                color: {color_hex} !important;
            }}

            /* Active link in sidebar (e.g. Dashboard, Admin Users, etc.) */
            #nav-sidebar-inner a.bg-base-100,
            #nav-sidebar-inner a[class*="font-semibold"],
            .dark #nav-sidebar-inner a.bg-base-100,
            .dark #nav-sidebar-inner a[class*="dark:bg-white"] {{
                color: {color_hex} !important;
            }}

            #nav-sidebar-inner a.bg-base-100 *,
            #nav-sidebar-inner a[class*="font-semibold"] *,
            .dark #nav-sidebar-inner a.bg-base-100 *,
            .dark #nav-sidebar-inner a[class*="dark:bg-white"] * {{
                color: {color_hex} !important;
            }}

            /* Sidebar link hover state */
            #nav-sidebar-inner a:hover,
            #nav-sidebar-inner a:hover *,
            .dark #nav-sidebar-inner a:hover,
            .dark #nav-sidebar-inner a:hover * {{
                color: {color_hex} !important;
            }}

            /* Collapsible sidebar group headers (e.g. User Management, Scan Management) */
            #nav-sidebar-inner h2:hover,
            #nav-sidebar-inner h2:hover *,
            #nav-sidebar-inner h2.group:hover *,
            #nav-sidebar-inner h2 [class*="group-hover:text-primary"],
            .dark #nav-sidebar-inner h2:hover,
            .dark #nav-sidebar-inner h2:hover *,
            .dark #nav-sidebar-inner h2 [class*="group-hover:text-primary"] {{
                color: {color_hex} !important;
            }}

            /* Header bar buttons & menu icons */
            header button[class*="text-primary"],
            header a[class*="text-primary"],
            header .material-symbols-outlined {{
                color: {color_hex} !important;
            }}
        </style>
    """)


def get_primary_colors_dict(request=None):
    color = get_system_color()
    return {
        "50": color,
        "100": color,
        "200": color,
        "300": color,
        "400": color,
        "500": color,
        "600": color,
        "700": color,
        "800": color,
        "900": color,
        "950": color,
    }


def get_unfold_settings():
    return {
        "COLORS": {
            "primary": lambda request=None: get_primary_colors_dict(request),
        },
        "STYLES": [
            lambda request: get_custom_unfold_css(request),
        ],
        "SITE_TITLE": lambda request: get_about_system().title,
        "SITE_HEADER": lambda request: get_about_system().title,
        "SITE_SUBHEADER": lambda request: get_about_system().title,
        "SITE_URL": "https://Vantafy.com",
        "SITE_LOGO": {
            "light": lambda request: get_about_system().logo.url,  # light mode
            "dark": lambda request: get_about_system().logo.url,  # dark mode
        },
        "SITE_SYMBOL": "speed",  # symbol from icon set
        "SITE_FAVICONS": [
            {
                "rel": "icon",
                "sizes": "32x32",
                "type": "image/svg+xml",
                "href": lambda request: get_about_system().favicon.url,
            },
        ],
        "DASHBOARD_CALLBACK": "apps.dashboard.views.dashboard_callback",
        "SHOW_HISTORY": True,  # show/hide "History" button, default: True
        "SHOW_VIEW_ON_SITE": True,  # show/hide "View on site" button, default: True
        "SHOW_BACK_BUTTON": True,  # show/hide "Back" button on changeform in header, default: False
        "THEME": "auto",
        "LOGIN": {
            "image": lambda request: static("sample/login-bg.jpg"),
            "redirect_after": lambda request: reverse_lazy(
                "admin:APP_MODEL_changelist"
            ),
        },
        "BORDER_RADIUS": "6px",
        "SIDEBAR": {
            "show_search": True,  # Search in applications and models names
            "show_all_applications": True,  # Dropdown with all applications and models
            "navigation": [
                {
                    "items": [
                        {
                            "title": _("Dashboard"),
                            "icon": "dashboard",
                            "link": reverse_lazy("admin:index"),
                            "permission": lambda request: request.user.is_superuser,
                        },
                    ],
                },
                {
                    "title": _("User Management"),
                    "separator": True,
                    "collapsible": True,
                    "items": [
                        {
                            "title": _("Admin Users"),
                            "icon": "admin_panel_settings",  # or "security"
                            "link": reverse_lazy("admin:user_admin_changelist"),
                            "description": _("System administrators and staff"),
                        },
                        {
                            "title": _("Individual Users"),
                            "icon": "person",  # or "person_outline"
                            "link": reverse_lazy("admin:user_individual_changelist"),
                            "description": _("Regular customer accounts"),
                        },
                        {
                            "title": _("Agency Accounts"),
                            "icon": "business",  # or "apartment"
                            "link": reverse_lazy("admin:user_agency_changelist"),
                            "description": _("Agency organization accounts"),
                        },
                        {
                            "title": _("Agency Members"),
                            "icon": "groups",  # or "people"
                            "link": reverse_lazy(
                                "admin:user_agencymemberlist_changelist"
                            ),
                            "description": _("Members belonging to agencies"),
                        },
                    ],
                },
                {
                    "title": _("Scan Management"),
                    "separator": True,
                    "collapsible": True,
                    "collapsed": True,
                    "items": [
                        {
                            "title": _("All Scans Overview"),
                            "icon": "auto_awesome_motion",
                            "link": reverse_lazy(
                                "admin:scanner_customerscanprocessing_allscans"
                            ),
                        },
                        {
                            "title": _("Scan Results"),
                            "icon": "check_circle",
                            "link": reverse_lazy(
                                "admin:scanner_customerscanusersummary_changelist"
                            ),
                        },
                        {
                            "title": _("Images"),
                            "icon": "image",
                            "link": reverse_lazy(
                                "admin:scanner_customerscanresultimage_changelist"
                            ),
                        },
                        {
                            "title": _("Links"),
                            "icon": "link",
                            "link": reverse_lazy(
                                "admin:scanner_customerscanresultpageurl_changelist"
                            ),
                        },
                    ],
                },
                {
                    "title": _("Individual User Scan Management"),
                    "separator": True,
                    "collapsible": True,
                    "collapsed": True,
                    "items": [
                        {
                            "title": _("Start Scan by Name"),
                            "icon": "search",
                            "link": reverse_lazy(
                                "admin:scanner_customerscanprocessing_scannow"
                            ),
                        },
                        {
                            "title": _("Scan Processes"),
                            "icon": "play_circle",
                            "link": reverse_lazy(
                                "admin:scanner_customerscanprocessing_changelist"
                            ),
                        },
                        {
                            "title": _("Scan Results"),
                            "icon": "check_circle",
                            "link": reverse_lazy(
                                "admin:scanner_customerscanusersummary_changelist"
                            ),
                        },
                        {
                            "title": _("Images"),
                            "icon": "image",
                            "link": reverse_lazy(
                                "admin:scanner_customerscanresultimage_changelist"
                            ),
                        },
                        {
                            "title": _("Links"),
                            "icon": "link",
                            "link": reverse_lazy(
                                "admin:scanner_customerscanresultpageurl_changelist"
                            ),
                        },
                    ],
                },
                {
                    "title": _("Agency Scan Management"),
                    "separator": True,
                    "collapsible": True,
                    "collapsed": True,
                    "items": [
                        {
                            "title": _("Scan Processes"),
                            "icon": "play_circle",
                            "link": reverse_lazy(
                                "admin:scanner_agencymemberscanprocessing_changelist"
                            ),
                        },
                        {
                            "title": _("Scan Results"),
                            "icon": "check_circle",
                            "link": reverse_lazy(
                                "admin:scanner_agencymemberscanusersummary_changelist"
                            ),
                        },
                        {
                            "title": _("Images"),
                            "icon": "image",
                            "link": reverse_lazy(
                                "admin:scanner_agencymemberscanresultimage_changelist"
                            ),
                        },
                        {
                            "title": _("Links"),
                            "icon": "link",
                            "link": reverse_lazy(
                                "admin:scanner_agencymemberscanresultpageurl_changelist"
                            ),
                        },
                    ],
                },
                {
                    "title": _("Link Removal Requests"),
                    "separator": True,
                    "collapsible": True,
                    "items": [
                        {
                            "title": _("From Customer"),
                            "icon": "support_agent",
                            "link": reverse_lazy(
                                "admin:scanner_linkremovalrequestfromcustomer_changelist"
                            ),
                        },
                        {
                            "title": _("From Agency Member"),
                            "icon": "support_agent",
                            "link": reverse_lazy(
                                "admin:scanner_linkremovalrequestfromagencymember_changelist"
                            ),
                        },
                    ],
                },
                {
                    "title": _("Customer Support"),
                    "separator": True,
                    "collapsible": True,
                    "items": [
                        {
                            "title": _("Support Tickets"),
                            "icon": "support_agent",
                            "link": reverse_lazy(
                                "admin:customer_support_message_changelist"
                            ),
                        },
                    ],
                },
                {
                    "title": _("Subscription Management"),
                    "separator": True,
                    "collapsible": True,
                    "items": [
                        {
                            "title": _("Features"),
                            "icon": "star",
                            "link": reverse_lazy(
                                "admin:subscriptions_feature_changelist"
                            ),
                        },
                        {
                            "title": _("Packages"),
                            "icon": "package",
                            "link": reverse_lazy(
                                "admin:subscriptions_package_changelist"
                            ),
                        },
                        {
                            "title": _("Subscriptions"),
                            "icon": "subscriptions",
                            "link": reverse_lazy(
                                "admin:subscriptions_subscription_changelist"
                            ),
                        },
                    ],
                },
                {
                    "title": _("Unauthorized Websites & Emails"),
                    "separator": True,
                    "collapsible": True,
                    "items": [
                        {
                            "title": _("Unauthorized Websites & Emails"),
                            "icon": "support_agent",
                            "link": reverse_lazy(
                                "admin:scanner_unauthorizedwebsiteandemail_changelist"
                            ),
                        },
                    ],
                },
                {
                    "title": _("System Setting"),
                    "separator": True,
                    "collapsible": True,
                    "items": [
                        {
                            "title": _("About System"),
                            "icon": "info",
                            "link": reverse_lazy(
                                "admin:system_setting_aboutsystem_changelist"
                            ),
                        },
                        {
                            "title": _("Social Media"),
                            "icon": "share",
                            "link": reverse_lazy(
                                "admin:system_setting_socialmedia_changelist"
                            ),
                        },
                        {
                            "title": _("SMTP Settings"),
                            "icon": "email",
                            "link": reverse_lazy(
                                "admin:system_setting_smtpsetting_changelist"
                            ),
                        },
                        {
                            "title": _("System Color"),
                            "icon": "palette",
                            "link": reverse_lazy(
                                "admin:system_setting_systemcolor_changelist"
                            ),
                        },
                    ],
                },
                {
                    "title": _("Page Management"),
                    "separator": True,
                    "collapsible": True,
                    "items": [
                        {
                            "title": _("Pages"),
                            "icon": "pages",
                            "link": reverse_lazy("admin:cms_page_changelist"),
                        },
                        {
                            "title": _("Available Niches"),
                            "icon": "category",
                            "link": reverse_lazy(
                                "admin:user_availableniche_changelist"
                            ),
                        },
                    ],
                },
                {
                    "title": _("Landing Page Management"),
                    "separator": True,
                    "collapsible": True,
                    "items": [
                        {
                            "title": _("Hero Section"),
                            "icon": "home",
                            "link": reverse_lazy("admin:cms_herosection_changelist"),
                        },
                        {
                            "title": _("Hero Radar"),
                            "icon": "radar",
                            "link": reverse_lazy("admin:cms_heroradaricon_changelist"),
                        },
                        {
                            "title": _("Represented Platforms"),
                            "icon": "apps",
                            "link": reverse_lazy(
                                "admin:cms_representplatform_changelist"
                            ),
                        },
                        {
                            "title": _("Our Customers"),
                            "icon": "group",
                            "link": reverse_lazy(
                                "admin:cms_amongourcustomer_changelist"
                            ),
                        },
                        {
                            "title": _("Testimonials"),
                            "icon": "star",
                            "link": reverse_lazy("admin:cms_testimonial_changelist"),
                        },
                        {
                            "title": _("How It Works"),
                            "icon": "lightbulb",
                            "link": reverse_lazy("admin:cms_howitworks_changelist"),
                        },
                        {
                            "title": _("Peace of Mind"),
                            "icon": "fingerprint",
                            "link": reverse_lazy(
                                "admin:cms_identitytracking_changelist"
                            ),
                        },
                        {
                            "title": _("Our Metrics"),
                            "icon": "analytics",
                            "link": reverse_lazy(
                                "admin:cms_ourmetrics_changelist"
                            ),
                        },
                    ],
                },
                {
                    "title": _("FAQ Management"),
                    "separator": True,
                    "collapsible": True,
                    "items": [
                        {
                            "title": _("FAQs"),
                            "icon": "help",
                            "link": reverse_lazy("admin:cms_faq_changelist"),
                        },
                    ],
                },
            ],
        },
    }
