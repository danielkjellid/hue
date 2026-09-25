from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=120)

    def __str__(self) -> str:
        return self.name


class Invoice(models.Model):
    class Status(models.TextChoices):
        PAID = "paid", "Paid"
        PENDING = "pending", "Pending"
        DECLINED = "declined", "Declined"
        DRAFT = "draft", "Draft"

    reference = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="invoices"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices)
    issued_on = models.DateField()
    archived = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.reference
