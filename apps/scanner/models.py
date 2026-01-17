import uuid
from django.db import models
from django.conf import settings


class ScanJob(models.Model):
    """Represents a scanning job to find media for a creator."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator_name = models.CharField(max_length=255, help_text="Name to search for")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='scan_jobs',
        null=True,
        blank=True,
        help_text="User who initiated the scan"
    )
    
    # Progress tracking
    total_spiders = models.IntegerField(default=0)
    completed_spiders = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Scan Job'
        verbose_name_plural = 'Scan Jobs'
    
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


class ScanResult(models.Model):
    """Stores results from a single spider for a scan job."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scan_job = models.ForeignKey(
        ScanJob,
        on_delete=models.CASCADE,
        related_name='results'
    )
    website = models.CharField(max_length=255, help_text="Spider/website name")
    images = models.JSONField(default=list, blank=True, help_text="List of image URLs")
    videos = models.JSONField(default=list, blank=True, help_text="List of video URLs")
    
    # Timestamps
    scraped_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-scraped_at']
        verbose_name = 'Scan Result'
        verbose_name_plural = 'Scan Results'
        unique_together = ['scan_job', 'website']
    
    def __str__(self):
        return f"{self.website} - {len(self.images or [])} images, {len(self.videos or [])} videos"