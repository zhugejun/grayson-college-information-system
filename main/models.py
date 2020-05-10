from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subjects = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f'<Profile {self.user.username}>'

# save user_id to profile when user was created
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()


class Subject(models.Model):

    name = models.CharField(max_length=4)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name
