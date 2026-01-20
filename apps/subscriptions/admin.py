from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Feature, Package, Subscription, PaymentHistory, IncomeReport


@admin.register(Feature)
class FeatureAdmin(ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Package)
class PackageAdmin(ModelAdmin):
    list_display = ['name', 'type', 'price', 'enabled']
    list_filter = ['type', 'enabled']
    search_fields = ['name']
    filter_horizontal = ['features']


@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    list_display = ['user', 'package', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'start_date', 'end_date']
    search_fields = ['user__email', 'stripe_subscription_id']
    date_hierarchy = 'created_at'


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(ModelAdmin):
    list_display = ['user', 'package', 'amount', 'payment_gateway', 'payment_status', 'paid_at']
    list_filter = ['payment_gateway', 'payment_status', 'paid_at']
    search_fields = ['user__email', 'transaction_id']
    date_hierarchy = 'paid_at'


@admin.register(IncomeReport)
class IncomeReportAdmin(ModelAdmin):
    list_display = ['total_income']
