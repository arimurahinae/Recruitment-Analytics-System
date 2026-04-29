"""
用户相关 HTTP API（注册、登录、当前用户、登出）。
与 `user.models.User`（AbstractUser 扩展字段）对齐。
"""

from __future__ import annotations

import functools
import json
import logging
from datetime import date, datetime
from typing import Any, Callable, Dict, Optional

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.db import DatabaseError, IntegrityError
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

User = get_user_model()
_signer = TimestampSigner(salt="liepin-recruit-auth")

_TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 14  # 14 天


def _json_body(request: HttpRequest) -> Dict[str, Any]:
    try:
        raw = request.body.decode("utf-8") or "{}"
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _parse_birth_date(value: Any) -> Optional[date]:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    s = str(value).strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def _normalize_gender(value: Any) -> Optional[str]:
    if value is None or value == "":
        return None
    s = str(value).strip().lower()
    allowed = {User.GENDER_UNKNOWN, User.GENDER_MALE, User.GENDER_FEMALE}
    if s in allowed:
        return s
    return None


def user_to_dict(user: User) -> Dict[str, Any]:
    """返回可序列化的用户资料（与模型字段对应）。"""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email or "",
        "phone": user.phone or "",
        "avatar": user.avatar or "",
        "gender": user.gender or User.GENDER_UNKNOWN,
        "birth_date": user.birth_date.isoformat() if user.birth_date else "",
        "bio": user.bio or "",
        "title": getattr(user, "profile_title", "") or "",
        "team": getattr(user, "profile_team", "") or "",
        "office": getattr(user, "profile_office", "") or "",
        "skills": getattr(user, "profile_skills", "") or "",
        "delivery_tag": getattr(user, "profile_delivery_tag", "") or "",
        "notify_email": bool(getattr(user, "notify_email", True)),
        "notify_sms": bool(getattr(user, "notify_sms", False)),
        "remember_device": bool(getattr(user, "remember_device", True)),
        "date_joined": user.date_joined.isoformat() if user.date_joined else "",
        "last_login": user.last_login.isoformat() if user.last_login else "",
        "created_at": user.created_at.isoformat() if getattr(user, "created_at", None) else "",
    }


def _issue_token(user: User) -> str:
    return _signer.sign(str(user.pk))


def _parse_bearer_token(request: HttpRequest) -> Optional[str]:
    h = request.headers.get("Authorization") or ""
    if h.startswith("Bearer "):
        return h[7:].strip() or None
    return None


def _user_from_token(token: str) -> Optional[User]:
    try:
        uid = _signer.unsign(token, max_age=_TOKEN_MAX_AGE_SECONDS)
        return User.objects.filter(pk=int(uid)).first()
    except (BadSignature, SignatureExpired, ValueError, TypeError):
        return None


def _error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"ok": False, "message": message}, status=status)


def _ok(data: Dict[str, Any], status: int = 200) -> JsonResponse:
    payload = {"ok": True, **data}
    return JsonResponse(payload, status=status)


def json_api(view_fn: Callable[..., JsonResponse]) -> Callable[..., JsonResponse]:
    """捕获未处理异常，返回 JSON（避免前端拿到 HTML 500 页）。"""

    @functools.wraps(view_fn)
    def _wrapped(request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        try:
            return view_fn(request, *args, **kwargs)
        except IntegrityError as e:
            logger.warning("IntegrityError in %s: %s", view_fn.__name__, e)
            return _error("数据冲突或约束失败，请检查用户名、手机号、邮箱是否重复")
        except DatabaseError as e:
            logger.exception("DatabaseError in %s", view_fn.__name__)
            hint = "请确认 MySQL 已启动、库表已 migrate（python manage.py migrate）。"
            detail = str(e) if settings.DEBUG else ""
            return JsonResponse(
                {"ok": False, "message": f"数据库异常。{hint}", "detail": detail},
                status=503,
            )
        except Exception as e:  # noqa: BLE001
            logger.exception("Unhandled error in %s", view_fn.__name__)
            return JsonResponse(
                {
                    "ok": False,
                    "message": "服务器内部错误",
                    "detail": str(e) if settings.DEBUG else "",
                },
                status=500,
            )

    return _wrapped


@csrf_exempt
@require_http_methods(["POST"])
@json_api
def api_register(request: HttpRequest) -> JsonResponse:
    """
    注册：仅要求用户名非空；密码不做强度校验；不返回 Token，需用户另行登录。
    email、phone 等仍可按需写入，不做格式校验与唯一性预检（冲突时由数据库约束返回错误）。
    """
    data = _json_body(request)
    username = (data.get("username") or "").strip()
    password = data.get("password")
    if password is None:
        password = ""
    elif not isinstance(password, str):
        password = str(password)
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()
    avatar_raw = (data.get("avatar") or "").strip()
    bio = (data.get("bio") or "").strip()
    gender_in = _normalize_gender(data.get("gender"))
    birth = _parse_birth_date(data.get("birth_date"))

    if not username:
        return _error("请填写用户名")
    if len(username) > 150:
        return _error("用户名过长")
    if avatar_raw and len(avatar_raw) > 500:
        return _error("头像地址过长")
    if bio and len(bio) > 5000:
        return _error("简介过长")

    kwargs: Dict[str, Any] = {
        "username": username,
        "password": password,
    }
    if email:
        kwargs["email"] = email
    if phone:
        kwargs["phone"] = phone
    if avatar_raw:
        kwargs["avatar"] = avatar_raw[:500]
    if bio:
        kwargs["bio"] = bio[:5000]
    if gender_in is not None:
        kwargs["gender"] = gender_in
    if birth is not None:
        kwargs["birth_date"] = birth

    try:
        user = User.objects.create_user(**kwargs)
    except IntegrityError:
        return _error("用户名、手机号或邮箱与已有记录冲突")
    except TypeError as e:
        return _error(str(e))

    logger.info("用户注册成功并已写入数据库: id=%s username=%s", user.pk, user.username)
    return _ok(
        {
            "message": "注册成功，请使用账号密码登录",
            "user": user_to_dict(user),
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
@json_api
def api_login(request: HttpRequest) -> JsonResponse:
    """
    登录：username + password；成功后签发 Token 并更新 last_login。
    """
    data = _json_body(request)
    username = (data.get("username") or "").strip()
    password = data.get("password")
    if password is None:
        password = ""
    elif not isinstance(password, str):
        password = str(password)

    if not username:
        return _error("请输入用户名")

    user = authenticate(request, username=username, password=password)
    if user is None:
        return _error("用户名或密码错误")

    if not user.is_active:
        return _error("账号已禁用", status=403)

    now = timezone.now()
    user.last_login = now
    user.save(update_fields=["last_login"])

    token = _issue_token(user)
    return _ok({"token": token, "user": user_to_dict(user)})


@csrf_exempt
@require_http_methods(["POST", "GET"])
@json_api
def api_logout(request: HttpRequest) -> JsonResponse:
    """
    无状态 Token：客户端删除本地 Token 即可；此处返回成功便于前端统一处理。
    """
    return _ok({})


@csrf_exempt
@require_http_methods(["GET", "PUT"])
@json_api
def api_me(request: HttpRequest) -> JsonResponse:
    """当前用户资料（需 Header: Authorization: Bearer <token>）。"""
    token = _parse_bearer_token(request)
    if not token:
        return _error("未登录", status=401)
    user = _user_from_token(token)
    if user is None:
        return _error("登录已失效", status=401)
    if not user.is_active:
        return _error("账号已禁用", status=403)
    if request.method == "GET":
        return _ok({"user": user_to_dict(user)})

    data = _json_body(request)

    username = data.get("username")
    if username is not None:
        username = str(username).strip()
        if not username:
            return _error("用户名不能为空")
        if len(username) > 150:
            return _error("用户名过长")
        user.username = username

    email = data.get("email")
    if email is not None:
        email = str(email).strip()
        if len(email) > 254:
            return _error("邮箱过长")
        user.email = email

    phone = data.get("phone")
    if phone is not None:
        phone = str(phone).strip()
        if phone == "":
            user.phone = None
        else:
            if len(phone) > 20:
                return _error("手机号过长")
            user.phone = phone

    avatar_raw = data.get("avatar")
    if avatar_raw is not None:
        avatar_raw = str(avatar_raw).strip()
        # 允许 URL 或 base64 DataURL，不限制长度（受数据库字段类型约束）
        user.avatar = avatar_raw

    bio = data.get("bio")
    if bio is not None:
        bio = str(bio)
        if len(bio) > 5000:
            return _error("简介过长")
        user.bio = bio

    title = data.get("title")
    if title is not None:
        title = str(title).strip()
        if len(title) > 40:
            return _error("职位/头衔过长")
        user.profile_title = title

    team = data.get("team")
    if team is not None:
        team = str(team).strip()
        if len(team) > 40:
            return _error("所属团队过长")
        user.profile_team = team

    office = data.get("office")
    if office is not None:
        office = str(office).strip()
        if len(office) > 40:
            return _error("办公地点过长")
        user.profile_office = office

    skills = data.get("skills")
    if skills is not None:
        skills = str(skills).strip()
        if len(skills) > 80:
            return _error("擅长标签过长")
        user.profile_skills = skills

    delivery_tag = data.get("delivery_tag")
    if delivery_tag is not None:
        delivery_tag = str(delivery_tag).strip()
        if len(delivery_tag) > 20:
            return _error("投递标签过长")
        user.profile_delivery_tag = delivery_tag

    if "notify_email" in data:
        user.notify_email = bool(data.get("notify_email"))
    if "notify_sms" in data:
        user.notify_sms = bool(data.get("notify_sms"))
    if "remember_device" in data:
        user.remember_device = bool(data.get("remember_device"))

    gender_in = data.get("gender")
    if gender_in is not None:
        g = _normalize_gender(gender_in)
        if g is None:
            return _error("性别参数不合法")
        user.gender = g

    birth_in = data.get("birth_date")
    if birth_in is not None:
        user.birth_date = _parse_birth_date(birth_in)

    try:
        user.save()
    except IntegrityError:
        return _error("用户名或手机号与已有用户冲突")

    return _ok({"message": "保存成功", "user": user_to_dict(user)})
