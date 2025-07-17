from django.db import models


# Create your models here.
class Contacts(models.Model):
    LINK_PRECEDENCE_CHOICES = [
        ("PM" , "primary"),
        ("SC" , "secondary"),
    ]

    id = models.AutoField(primary_key=True)
    phoneNumber = models.CharField(max_length=10, unique=True, blank=True, null=True,default=None)
    email = models.EmailField(null=True,unique=True, default=None)
    linkedId = models.IntegerField(null=True, blank=True, default=None)
    linkPrecedence = models.CharField(choices=LINK_PRECEDENCE_CHOICES)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateField(auto_now_add=True)
    deletedAt = models.DateField(null=True, blank=True, default=None)

    