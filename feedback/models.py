from django.db import models
from accounts.models import Login


class Feedback(models.Model):
    feedback_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Login, on_delete=models.CASCADE)
    feedback_text = models.TextField()
    emoji_rating = models.CharField(max_length=20, blank=True)
    feedback_date = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'feedback_feedback'
        ordering = ['-feedback_date', '-feedback_id']

    def __str__(self):
        return f"Feedback #{self.feedback_id}"
