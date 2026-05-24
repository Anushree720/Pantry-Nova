from django.db import models
from accounts.models import Login


class Complaint(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('replied', 'Replied'),
    ]

    complaint_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Login, on_delete=models.CASCADE)
    complaint_text = models.TextField()
    reply_text = models.TextField(blank=True)
    complaint_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    class Meta:
        db_table = 'complaints_complaint'
        ordering = ['-complaint_date', '-complaint_id']

    def __str__(self):
        return f"Complaint #{self.complaint_id} ({self.status})"
