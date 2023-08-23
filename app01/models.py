from django.db import models

# Create your models here.


class allMistakesNew(models.Model):
    nameOfRadio = models.CharField(max_length=32)
    date = models.DateField(null=True)
    details = models.CharField(max_length=128)
    keyword = models.CharField(max_length=32,default='default',null=True)

class AiWordsTrial(models.Model):
    linkWord= models.CharField(max_length=32)


class allMandD(models.Model):
    nameOfRadio = models.CharField(max_length=32)
    timePoints= models.CharField(max_length=256)
    date = models.DateField(null=True)

class timePoints(models.Model):
    timePoints = models.CharField(max_length=256)