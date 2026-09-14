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
    customer = models.ForeignKey(User,on_delete=models.CASCADE,related_name='customer_scan_processes', null=True, blank=True)
    custom_search_name = models.CharField(max_length=255, blank=True, null=True, help_text="Custom name queried for this scan job")
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
    
    def get_result_model(self):
        return CustomerScanResult
    
    @property
    def search_name(self):
        if self.custom_search_name:
            return self.custom_search_name
        if self.customer and self.customer.full_name:
            return self.customer.full_name
        return "Unknown"

    def __str__(self):
        return f"{self.search_name} - {self.status}"
    
    @property
    def progress_percentage(self):
        if self.total_spiders == 0:
            return 0
        return round((self.completed_spiders / self.total_spiders) * 100, 1)
    
    @property
    def total_images(self):
        if hasattr(self, 'num_images'):
            return self.num_images
        return sum(result.total_images for result in self.results.all())
    
    @property
    def total_videos(self):
        if hasattr(self, 'num_videos'):
            return self.num_videos
        return sum(result.total_videos for result in self.results.all())
    
    @property
    def total_page_urls(self):
        if hasattr(self, 'num_page_urls'):
            return self.num_page_urls
        return sum(result.total_page_urls for result in self.results.all())




class CustomerScanResult(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('action_taken', 'Action Taken'),
        ('ignored', 'Ignored'),
    ]

    customer = models.ForeignKey(User,on_delete=models.CASCADE,related_name='customer_scan_results', null=True, blank=True)
    # Link back to the processing job
    scan_job = models.ForeignKey(CustomerScanProcessing, on_delete=models.CASCADE, related_name='results', null=True, blank=True)
    
    website = models.CharField(max_length=255, help_text="Spider/website name")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Extra data found
    profile_url = models.URLField(max_length=500, blank=True, null=True)
    contact_emails = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def total_images(self):
        if hasattr(self, 'num_images'):
            return self.num_images
        return self.image_entries.count()

    @property
    def total_videos(self):
        if hasattr(self, 'num_videos'):
            return self.num_videos
        return self.video_entries.count()

    @property
    def total_page_urls(self):
        if hasattr(self, 'num_page_urls'):
            return self.num_page_urls
        return self.page_url_entries.count()
    
    def add_image(self, original_url, content=None):
        from django.core.files.base import ContentFile
        import os
        
        # Skip if this image URL already exists for this scan result
        if self.image_entries.filter(image_url=original_url).exists():
            return self.image_entries.filter(image_url=original_url).first()
        
        img_entry = CustomerScanResultImage(
            customer_scan_result=self,
            image_url=original_url
        )
        if content:
            filename = os.path.basename(original_url) or f"image_{uuid.uuid4()}.jpg"
            if len(filename) > 100: filename = filename[-100:]
            img_entry.image.save(filename, ContentFile(content), save=False)
        
        img_entry.save()
        return img_entry

    def add_video(self, video_url):
        obj, created = CustomerScanResultVideo.objects.get_or_create(
            customer_scan_result=self,
            video_url=video_url
        )
        return obj
        
    def add_page_url(self, page_url):
        obj, created = CustomerScanResultPageUrl.objects.get_or_create(
            customer_scan_result=self,
            page_url=page_url
        )
        return obj

    class Meta:
        unique_together = ('customer', 'website')

    def __str__(self):
        return self.website


class CustomerScanResultImage(models.Model):
    customer_scan_result = models.ForeignKey(CustomerScanResult, on_delete=models.CASCADE, related_name='image_entries')
    image_url = models.URLField(max_length=500)
    image = models.ImageField(upload_to='customer_scan_images/', blank=True, null=True)

    class Meta:
        unique_together = ('customer_scan_result', 'image_url')

    def __str__(self):
        return self.image_url
    
class CustomerScanResultVideo(models.Model):
    customer_scan_result = models.ForeignKey(CustomerScanResult, on_delete=models.CASCADE, related_name='video_entries')
    video_url = models.URLField(max_length=500)
    video = models.FileField(upload_to='customer_scan_videos/', blank=True, null=True)
    

    class Meta:
        unique_together = ('customer_scan_result', 'video_url')

    def __str__(self):
        return self.video_url
    

class CustomerScanResultPageUrl(models.Model):
    MAIL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
    ]
    customer_scan_result = models.ForeignKey(CustomerScanResult, on_delete=models.CASCADE, related_name='page_url_entries')
    page_url = models.URLField(max_length=500)
    send_mail_status = models.CharField(max_length=20, choices=MAIL_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        unique_together = ('customer_scan_result', 'page_url')

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
    custom_search_name = models.CharField(max_length=255, blank=True, null=True, help_text="Custom name queried for this scan job")
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
    
    def get_result_model(self):
        return AgencyMemberScanResult
    
    @property
    def search_name(self):
        if self.custom_search_name:
            return self.custom_search_name
        if self.agency_member and self.agency_member.name:
            return self.agency_member.name
        return "Unknown"

    def __str__(self):
        return f"{self.search_name} - {self.status}"
    
    @property
    def progress_percentage(self):
        if self.total_spiders == 0:
            return 0
        return round((self.completed_spiders / self.total_spiders) * 100, 1)
    
    @property
    def total_images(self):
        if hasattr(self, 'num_images'):
            return self.num_images
        return sum(result.total_images for result in self.results.all())
    
    @property
    def total_videos(self):
        if hasattr(self, 'num_videos'):
            return self.num_videos
        return sum(result.total_videos for result in self.results.all())

    @property
    def total_page_urls(self):
        if hasattr(self, 'num_page_urls'):
            return self.num_page_urls
        return sum(result.total_page_urls for result in self.results.all())
    
    


class AgencyMemberScanResult(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('action_taken', 'Action Taken'),
        ('ignored', 'Ignored'),
    ]

    agency = models.ForeignKey(User,on_delete=models.CASCADE,related_name='agency_member_scan_results',)
    agency_member = models.ForeignKey(AgencyMemberList,on_delete=models.CASCADE,related_name='agency_member_scan_results',)
    # Link back to processing job
    scan_job = models.ForeignKey(AgencyMemberScanProcessing, on_delete=models.CASCADE, related_name='results', null=True, blank=True)

    website = models.CharField(max_length=255, help_text="Spider/website name")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Extra data found
    profile_url = models.URLField(max_length=500, blank=True, null=True)
    contact_emails = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def total_images(self):
        if hasattr(self, 'num_images'):
            return self.num_images
        return self.image_entries.count()

    @property
    def total_videos(self):
        if hasattr(self, 'num_videos'):
            return self.num_videos
        return self.video_entries.count()

    @property
    def total_page_urls(self):
        if hasattr(self, 'num_page_urls'):
            return self.num_page_urls
        return self.page_url_entries.count()
        
    def add_image(self, original_url, content=None):
        from django.core.files.base import ContentFile
        import os
        
        # Skip if this image URL already exists for this scan result
        if self.image_entries.filter(image_url=original_url).exists():
            return self.image_entries.filter(image_url=original_url).first()
        
        img_entry = AgencyMemberScanResultImage(
            agency_member_scan_result=self,
            image_url=original_url
        )
        if content:
            filename = os.path.basename(original_url) or f"image_{uuid.uuid4()}.jpg"
            if len(filename) > 100: filename = filename[-100:]
            img_entry.image.save(filename, ContentFile(content), save=False)
        
        img_entry.save()
        return img_entry

    def add_video(self, video_url):
        obj, created = AgencyMemberScanResultVideo.objects.get_or_create(
            agency_member_scan_result=self,
            video_url=video_url
        )
        return obj
        
    def add_page_url(self, page_url):
        obj, created = AgencyMemberScanResultPageUrl.objects.get_or_create(
            agency_member_scan_result=self,
            page_url=page_url
        )
        return obj

    class Meta:
        unique_together = ('agency_member', 'website')


class AgencyMemberScanResultImage(models.Model):
    agency_member_scan_result = models.ForeignKey(AgencyMemberScanResult, on_delete=models.CASCADE, related_name='image_entries')
    image_url = models.URLField(max_length=500, default="")
    image = models.ImageField(upload_to='agency_member_scan_images/', blank=True, null=True)

    class Meta:
        unique_together = ('agency_member_scan_result', 'image_url')

    def __str__(self):
        return self.image_url
    
class AgencyMemberScanResultVideo(models.Model):
    agency_member_scan_result = models.ForeignKey(AgencyMemberScanResult, on_delete=models.CASCADE, related_name='video_entries')
    video_url = models.URLField(max_length=500, default="")
    video = models.FileField(upload_to='agency_member_scan_videos/', blank=True, null=True)

    class Meta:
        unique_together = ('agency_member_scan_result', 'video_url')

    def __str__(self):
        return self.video_url
    

class AgencyMemberScanResultPageUrl(models.Model):
    MAIL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
    ]
    agency_member_scan_result = models.ForeignKey(AgencyMemberScanResult, on_delete=models.CASCADE, related_name='page_url_entries')
    page_url = models.URLField(max_length=500, default="")
    send_mail_status = models.CharField(max_length=20, choices=MAIL_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        unique_together = ('agency_member_scan_result', 'page_url')

    def __str__(self):
        return self.page_url


class LinkRemovalRequestFromCustomer(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('removed', 'Removed'),
        ('failed', 'Failed'),
    ]
    LINKS_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='link_requested_for_removal_by_customer', null=True, blank=True)
    link = models.URLField(max_length=500, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    links = models.CharField(max_length=20, choices=LINKS_STATUS_CHOICES, default='pending', help_text="Email submission status: pending or submitted")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.customer.email if self.customer else self.link

class LinkRemovalRequestFromAgencyMember(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('removed', 'Removed'),
        ('failed', 'Failed'),
    ]
    LINKS_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
    ]

    agency = models.ForeignKey(User, on_delete=models.CASCADE, related_name='link_requested_for_removal', null=True, blank=True)
    agency_member = models.ForeignKey(AgencyMemberList, on_delete=models.CASCADE, related_name='link_requested_for_removal_by_agency', null=True, blank=True)
    link = models.URLField(max_length=500, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    links = models.CharField(max_length=20, choices=LINKS_STATUS_CHOICES, default='pending', help_text="Email submission status: pending or submitted")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.agency_member.name if self.agency_member else self.link
        return self.agency_member.name




class UnauthorizedWebsiteAndEmail(models.Model):
    website = models.CharField(max_length=255, unique=True)
    email = models.EmailField()
    
    def __str__(self):
        return self.website


class LinkRemovalVerification(models.Model):
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('available', 'Available'),
        ('removed', 'Removed'),
        ('redirected', 'Redirected'),
        ('temporarily_unavailable', 'Temporarily Unavailable'),
        ('blocked', 'Blocked'),
        ('unverified', 'Unverified'),
    ]

    customer_request = models.ForeignKey(
        LinkRemovalRequestFromCustomer,
        on_delete=models.CASCADE,
        related_name='verifications',
        null=True,
        blank=True
    )
    agency_request = models.ForeignKey(
        LinkRemovalRequestFromAgencyMember,
        on_delete=models.CASCADE,
        related_name='verifications',
        null=True,
        blank=True
    )
    url = models.URLField(max_length=500)
    http_status_code = models.IntegerField(null=True, blank=True)
    final_url = models.URLField(max_length=500, null=True, blank=True)
    content_type = models.CharField(max_length=100, null=True, blank=True)
    verification_status = models.CharField(
        max_length=30,
        choices=VERIFICATION_STATUS_CHOICES,
        default='pending'
    )
    retry_count = models.IntegerField(default=0)
    checked_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-checked_at']

    def __str__(self):
        return f"{self.url} -> {self.verification_status} ({self.http_status_code})"


class CustomerScanUserSummary(User):
    class Meta:
        proxy = True
        verbose_name = "Customer Scan Result"
        verbose_name_plural = "Customer Scan Results"


class AgencyMemberScanUserSummary(AgencyMemberList):
    class Meta:
        proxy = True
        verbose_name = "Agency Member Scan Result"
        verbose_name_plural = "Agency Member Scan Results"





