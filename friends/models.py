from django.db import models

from accounts.models import CustomUser


# Create your models here.
class FriendsRequests(models.Model):
    request_id = models.ForeignKey(CustomUser, related_name="requests", on_delete=models.CASCADE)
    receive_id = models.ForeignKey(CustomUser, related_name="receives", on_delete=models.CASCADE)
    status = models.CharField(max_length=10,
                              choices=(
                                  ("pending", "pending"),
                                  ("rejected", "rejected")
                              ),
                              default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("request_id", "receive_id")
        constraints = [models.CheckConstraint(
            check=~models.Q(request_id=models.F("receive_id")),
            name="check_request_id_not_receive_id")]

    def __str__(self):
        return f"{self.request_id} -> {self.receive_id} ({self.status})"


class Friends(models.Model):
    user1_id = models.ForeignKey(CustomUser, related_name="user1_id", on_delete=models.CASCADE)
    user2_id = models.ForeignKey(CustomUser, related_name="user2_id", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = (
            "user1_id",
            "user2_id",
        )
        constraints = [
            models.CheckConstraint(
                check=models.Q(user1_id__lt=models.F("user2_id")),
                name="check_user1_less_than_user2"
            )
        ]

    def __str__(self):
        return f"Friendship: {self.user1_id} and {self.user2_id}"