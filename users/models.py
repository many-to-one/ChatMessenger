from django.db import models

from django.contrib.auth.models import(
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        print('create_user ---------------------------', username, email, password)
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username)
        user.set_password(password)
        user.save()
        # user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password):
        user = self.create_user(email, username, password=password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        # user.save(using=self._db)
        return user
    

class CustomUser(AbstractBaseUser, PermissionsMixin):

    username=models.CharField(
        max_length=25,
        unique=True,
        null=True,
        db_index=True
    )
    email=models.EmailField(
        max_length=25,
        unique=True,
        null=True,
        db_index=True
    )
    photo=models.ImageField(
        upload_to='profile_photos/',
        default='profile_photos/profile.png',
        null=True, blank=True
        )
    friends = models.ManyToManyField(
        'self',
        symmetrical=True,
        )
    token = models.CharField(
        null=True,
        max_length=108,
    )
    login_at = models.DateTimeField(
        null=True,
        auto_now_add=True
        )
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(
        default=False
        )
    is_logged = models.BooleanField(
        default=False
        )
    is_staff = models.BooleanField(
        default=False
        )
    is_active = models.BooleanField(
        default=False
        )
    is_superuser = models.BooleanField(
        default=False
        )
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username
    

class BlackListToken(models.Model):
    token = models.CharField(
        null=True,
        max_length=108,
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE
        )

    def __str__(self) -> str:
        return self.user.username
