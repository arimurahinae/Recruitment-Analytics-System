from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    GENDER_UNKNOWN = "unknown"
    GENDER_MALE = "male"
    GENDER_FEMALE = "female"

    GENDER_CHOICES = (
        (GENDER_UNKNOWN, "未知"),
        (GENDER_MALE, "男"),
        (GENDER_FEMALE, "女"),
    )

    phone = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="手机号")
    avatar = models.TextField(blank=True, verbose_name="头像")
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        default=GENDER_UNKNOWN,
        verbose_name="性别",
    )
    birth_date = models.DateField(null=True, blank=True, verbose_name="出生日期")
    bio = models.TextField(blank=True, verbose_name="简介")

    # 个人资料扩展
    profile_title = models.CharField(max_length=40, blank=True, verbose_name="职位/头衔")
    profile_team = models.CharField(max_length=40, blank=True, verbose_name="所属团队")
    profile_office = models.CharField(max_length=40, blank=True, verbose_name="办公地点")
    profile_skills = models.CharField(max_length=80, blank=True, verbose_name="擅长标签")
    profile_delivery_tag = models.CharField(max_length=20, blank=True, verbose_name="投递标签")
    notify_email = models.BooleanField(default=True, verbose_name="邮件提醒")
    notify_sms = models.BooleanField(default=False, verbose_name="短信提醒")
    remember_device = models.BooleanField(default=True, verbose_name="记住设备")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="注册时间")
    last_login = models.DateTimeField(null=True, blank=True, verbose_name="最后登录时间")

    class Meta:
        db_table = "user_user"
        verbose_name = "用户"
        verbose_name_plural = "用户"
        indexes = [
            models.Index(fields=["username"], name="idx_user_username"),
            models.Index(fields=["phone"], name="idx_user_phone"),
            models.Index(fields=["email"], name="idx_user_email"),
        ]

    def __str__(self):
        return self.username
