from typing import Generic, TypeVar

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

T = TypeVar('T', bound=AbstractBaseUser)


class UserManager(BaseUserManager, Generic[T]):
    def create_user(self, username: str, password: str) -> AbstractBaseUser:
        user = self.model(username=username, is_superuser=False)
        user.password = make_password(password)
        user.save()
        return user

    def create_superuser(self, username: str, password: str) -> AbstractBaseUser:
        user = self.model(username=username, is_staff=True, is_superuser=True)
        user.password = make_password(password)
        user.save()
        return user


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        _('Username'),
        max_length=150,
        unique=True,
    )
    is_staff = models.BooleanField(
        _('Is staff'),
        default=False,
    )

    objects = UserManager()

    USERNAME_FIELD = 'username'

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
