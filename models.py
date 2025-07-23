from django.db import models

class RealTimeLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    src_ip = models.GenericIPAddressField(null=True, blank=True)
    dst_ip = models.GenericIPAddressField(null=True, blank=True)
    protocol = models.CharField(max_length=50, null=True, blank=True)
    prediction = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.timestamp} - {self.src_ip} → {self.dst_ip} | {self.prediction}"
    
