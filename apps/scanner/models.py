import uuid
from django.db import models
from apps.user.models import AgencyMemberList,User


class CustomerScanProcessing(models.Model):
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    customer = models.ForeignKey(User,on_delete=models.CASCADE,related_name='customer_scan_processes',)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Progress tracking
    total_spiders = models.IntegerField(default=0)
    completed_spiders = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True, null=True)
    
    
    def __str__(self):
        return f"{self.creator_name} - {self.status}"
    
    @property
    def progress_percentage(self):
        if self.total_spiders == 0:
            return 0
        return round((self.completed_spiders / self.total_spiders) * 100, 1)
    
    @property
    def total_images(self):
        return sum(len(result.images or []) for result in self.results.all())
    
    @property
    def total_videos(self):
        return sum(len(result.videos or []) for result in self.results.all())
    
    @property
    def total_page_urls(self):
        return sum(len(result.page_urls or []) for result in self.results.all())




class CustomerScanResult(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('action_taken', 'Action Taken'),
        ('ignored', 'Ignored'),
    ]

    customer = models.ForeignKey(User,on_delete=models.CASCADE,related_name='customer_scan_results',)
    website = models.CharField(max_length=255, help_text="Spider/website name")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    
    def __str__(self):
        return self.website


class CustomerScanResultImage(models.Model):
    customer_scan_result = models.ForeignKey(CustomerScanResult, on_delete=models.CASCADE, related_name='image_entries')
    image_url = models.URLField(max_length=500)
    image = models.ImageField(upload_to='customer_scan_images/')

    def __str__(self):
        return self.image_url
    
class CustomerScanResultVideo(models.Model):
    customer_scan_result = models.ForeignKey(CustomerScanResult, on_delete=models.CASCADE, related_name='video_entries')
    video_url = models.URLField(max_length=500)

    def __str__(self):
        return self.video_url
    

class CustomerScanResultPageUrl(models.Model):
    customer_scan_result = models.ForeignKey(CustomerScanResult, on_delete=models.CASCADE, related_name='page_url_entries')
    page_url = models.URLField(max_length=500)

    def __str__(self):
        return self.page_url


        
class AgencyMemberScanProcessing(models.Model):
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    agency = models.ForeignKey(User,on_delete=models.CASCADE,related_name='agency_scan_processes',)
    agency_member = models.ForeignKey(AgencyMemberList,on_delete=models.CASCADE,related_name='agency_member_scan_processes',)
    creator_name = models.CharField(max_length=255, help_text="Name to search for")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Progress tracking
    total_spiders = models.IntegerField(default=0)
    completed_spiders = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True, null=True)
    
    
    def __str__(self):
        return f"{self.creator_name} - {self.status}"
    
    @property
    def progress_percentage(self):
        if self.total_spiders == 0:
            return 0
        return round((self.completed_spiders / self.total_spiders) * 100, 1)
    
    @property
    def total_images(self):
        return sum(len(result.images or []) for result in self.results.all())
    
    @property
    def total_videos(self):
        return sum(len(result.videos or []) for result in self.results.all())

    @property
    def total_page_urls(self):
        return sum(len(result.page_urls or []) for result in self.results.all())
    




class AgencyMemberScanResult(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('action_taken', 'Action Taken'),
        ('ignored', 'Ignored'),
    ]

    agency = models.ForeignKey(User,on_delete=models.CASCADE,related_name='agency_member_scan_results',)
    agency_member = models.ForeignKey(AgencyMemberList,on_delete=models.CASCADE,related_name='agency_member_scan_results',)
    website = models.CharField(max_length=255, help_text="Spider/website name")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    
    
    

class AgencyMemberScanResultImage(models.Model):
    agency_member_scan_result = models.ForeignKey(AgencyMemberScanResult, on_delete=models.CASCADE, related_name='image_entries')
    image_url = models.URLField(max_length=500)
    image = models.ImageField(upload_to='agency_member_scan_images/')

    def __str__(self):
        return self.image_url
    
class AgencyMemberScanResultVideo(models.Model):
    agency_member_scan_result = models.ForeignKey(AgencyMemberScanResult, on_delete=models.CASCADE, related_name='video_entries')
    video_url = models.URLField(max_length=500)

    def __str__(self):
        return self.video_url
    

class AgencyMemberScanResultPageUrl(models.Model):
    agency_member_scan_result = models.ForeignKey(AgencyMemberScanResult, on_delete=models.CASCADE, related_name='page_url_entries')
    page_url = models.URLField(max_length=500)

    def __str__(self):
        return self.page_url






class UnauthorizedWebsiteAndEmail(models.Model):
    website = models.CharField(max_length=255, unique=True)
    email = models.EmailField()
    
    def __str__(self):
        return self.website


