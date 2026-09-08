# screening/backends.py

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from .models import PHCWorker

class PHCWorkerBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        try:
            worker = PHCWorker.objects.get(phc_id=username)
            user = worker.user
        except PHCWorker.DoesNotExist:
            try:
                worker = PHCWorker.objects.get(phone_number=username)
                user = worker.user
            except PHCWorker.DoesNotExist:
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    user = User.objects.filter(email__iexact=username).first()
                    if user is None:
                        return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None