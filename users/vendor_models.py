from django.db import models


class VendorCompany(models.Model):
    """
    Model representing a vendor company with access credentials.
    """
    name = models.CharField(max_length=255, unique=True)
    access_code = models.CharField(max_length=100, help_text="Hasło dostępu dla rejestracji dostawcy")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'firma dostawcy'
        verbose_name_plural = 'firmy dostawców'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def verify_access_code(self, code):
        """Verify if provided access code matches."""
        return self.access_code == code
