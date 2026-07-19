from django.db import models

# Create your models here.


class Sale(models.Model):
    factnum = models.CharField(max_length=1000, unique=True)
    dat = models.DateField()  # the date of sale
    total = models.DecimalField(max_digits=22, decimal_places=2)
    kname = models.CharField(max_length=1000)  # customer name
    tel = models.CharField(max_length=30)
    address = models.TextField()

    def __str__(self):
        return f"{self.kname} - {self.factnum}"