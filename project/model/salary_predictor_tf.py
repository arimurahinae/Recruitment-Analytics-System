from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import numpy as np
import re
import json
import random

# -----------------------------
# TensorFlow import guard (Windows)
# -----------------------------


def _tf_env_guard() -> None:
    """Set env vars before importing tensorflow to reduce Windows crashes.

    Notes:
    - Some Windows setups may crash (0xC0000005) when TensorFlow loads oneDNN/OpenMP.
    - These env vars are safe defaults for stability-first training.
    """

    import os

    os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    # Avoid OpenMP duplicate init crashes on some environments
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

# -----------------------------
# Feature schema
# -----------------------------


@dataclass
class SalaryFeatures:
    """Input features for salary prediction.

    Notes:
    - Text fields can be empty strings.
    - Numeric fields can be None; they will be imputed to 0.0 by the input pipeline.
    """

    job_title: str = ""
    job_desc: str = ""
    company: str = ""
    industry: str = ""
    city: str = ""
    work_years: str = ""  # keep as text token, e.g. "1-3年"
    edu: str = ""  # e.g. "本科"

    # Optional numeric signals (extend freely)
    salary_min_k: Optional[float] = None
    salary_max_k: Optional[float] = None


@dataclass
class TrainConfig:
    """Training config for salary predictor."""

    # data
    limit: Optional[int] = None
    min_samples: int = 200
    val_ratio: float = 0.12
    seed: int = 42

    # model
    text_encoder: str = "use"  # "use" (TF-Hub USE) or "avg_embed" (TextVectorization+Embedding)
    vocab_size: int = 30000
    seq_len: int = 96
    embed_dim: int = 128
    hidden: int = 192
    lr: float = 8e-4

    # training
    batch_size: int = 256
    epochs: int = 10
    patience: int = 3
    verbose: int = 2

    # save
    out_dir: str = "artifacts/salary_model"


def _safe_float(x: Any) -> float:
    if x is None:
        return 0.0
    try:
        return float(x)
    except Exception:
        return 0.0


def _ensure_1d_str(arr: Sequence[str]) -> np.ndarray:
    return np.asarray([("" if a is None else str(a)) for a in arr], dtype=object)


_RE_WS = re.compile(r"\s+")
_RE_HTML = re.compile(r"<[^>]+>")
_RE_CTRL = re.compile(r"[\u0000-\u001f\u007f]")
_RE_EMOJI = re.compile(
    r"[\U00010000-\U0010ffff]",
    flags=re.UNICODE,
)


def clean_text(s: Any, *, max_len: int = 2000) -> str:
    """Lightweight text cleaning for Chinese job text."""
    if s is None:
        return ""
    s = str(s)
    s = _RE_HTML.sub(" ", s)
    s = _RE_CTRL.sub(" ", s)
    # keep Chinese; drop astral-plane emojis/symbols that may bloat vocab
    s = _RE_EMOJI.sub(" ", s)
    s = s.replace("\u3000", " ")
    s = _RE_WS.sub(" ", s).strip()
    if len(s) > max_len:
        s = s[:max_len]
    return s


def _clamp_salary_k(x: float) -> float:
    # guardrails in K units
    if not np.isfinite(x):
        return 0.0
    return float(max(0.0, min(300.0, x)))


def _ensure_min_max(min_k: float, max_k: float) -> Tuple[float, float]:
    min_k = _clamp_salary_k(min_k)
    max_k = _clamp_salary_k(max_k)
    if max_k and min_k and max_k < min_k:
        min_k, max_k = max_k, min_k
    if max_k == 0.0 and min_k > 0.0:
        max_k = min_k
    return min_k, max_k


def parse_salary_to_k(salary_text: Any) -> Tuple[Optional[float], Optional[float]]:
    """Parse salary string into (min_k, max_k).

    Supports typical patterns:
    - "20-30K"
    - "20-30k·13薪"
    - "25K以上"
    - "30-50万/年" (approx -> convert to K/month if possible)
    - "面议" -> (None, None)
    """
    if salary_text is None:
        return None, None
    s = str(salary_text).strip()
    if not s or "面议" in s:
        return None, None

    s2 = s.replace(" ", "").replace("￥", "").replace("元", "")

    # 年薪：万/年
    m = re.search(r"(\d+(?:\.\d+)?)[-~](\d+(?:\.\d+)?)(万)/年", s2, flags=re.I)
    if m:
        a = float(m.group(1))
        b = float(m.group(2))
        # rough convert: 万/年 -> K/月, 1万=10K
        min_k = a * 10.0 / 12.0
        max_k = b * 10.0 / 12.0
        return _ensure_min_max(min_k, max_k)

    # 月薪 K
    m = re.search(r"(\d+(?:\.\d+)?)[-~](\d+(?:\.\d+)?)[kK]", s2)
    if m:
        return _ensure_min_max(float(m.group(1)), float(m.group(2)))

    # 单值 K
    m = re.search(r"(\d+(?:\.\d+)?)[kK](以上|起)?", s2)
    if m:
        v = float(m.group(1))
        return _ensure_min_max(v, v)

    # 月薪：万/月
    m = re.search(r"(\d+(?:\.\d+)?)[-~](\d+(?:\.\d+)?)(万)/月", s2, flags=re.I)
    if m:
        a = float(m.group(1)) * 10.0
        b = float(m.group(2)) * 10.0
        return _ensure_min_max(a, b)

    # 兜底：抓取数字
    nums = re.findall(r"\d+(?:\.\d+)?", s2)
    if len(nums) >= 2:
        a = float(nums[0])
        b = float(nums[1])
        # heuristic: if looks like 2-3 (万) treat as 万/月
        if "万" in s2 and "年" not in s2:
            return _ensure_min_max(a * 10.0, b * 10.0)
        # otherwise assume K
        return _ensure_min_max(a, b)
    if len(nums) == 1:
        v = float(nums[0])
        if "万" in s2 and "年" not in s2:
            v = v * 10.0
        return _ensure_min_max(v, v)
    return None, None


def _as_np_batch(features: Sequence[SalaryFeatures]) -> Dict[str, np.ndarray]:
    return {
        "text_main": _ensure_1d_str(
            [clean_text(f"{f.job_title} {f.job_desc}".strip(), max_len=2600) for f in features]
        ),
        "text_company": _ensure_1d_str([clean_text(f"{f.company} {f.industry}".strip(), max_len=600) for f in features]),
        "text_context": _ensure_1d_str([clean_text(f"{f.city} {f.work_years} {f.edu}".strip(), max_len=80) for f in features]),
        "num": np.asarray(
            [[_safe_float(f.salary_min_k), _safe_float(f.salary_max_k)] for f in features],
            dtype=np.float32,
        ),
    }


def build_tf_model(
    *,
    vocab_size: int = 20000,
    seq_len: int = 80,
    embed_dim: int = 96,
    num_dim: int = 2,
    hidden: int = 128,
    lr: float = 1e-3,
):
    """Build a multi-input TensorFlow model.

    Architecture:
    - 3 text inputs -> TextVectorization -> Embedding -> GlobalAveragePooling
    - 1 numeric input -> Dense stack
    - concat -> Dense -> regression head (predict salary_min_k, salary_max_k)

    Returns (model, vectorizers) where vectorizers is a dict of TextVectorization layers.
    """

    _tf_env_guard()
    import tensorflow as tf  # local import: keeps module import light if TF missing

    # Text inputs
    text_main_in = tf.keras.Input(shape=(1,), dtype=tf.string, name="text_main")
    text_company_in = tf.keras.Input(shape=(1,), dtype=tf.string, name="text_company")
    text_context_in = tf.keras.Input(shape=(1,), dtype=tf.string, name="text_context")

    def make_vec(name: str):
        return tf.keras.layers.TextVectorization(
            max_tokens=vocab_size,
            output_mode="int",
            output_sequence_length=seq_len,
            name=f"vec_{name}",
        )

    vec_main = make_vec("main")
    vec_company = make_vec("company")
    vec_context = make_vec("context")

    def text_tower(x, vec, tower_name: str):
        x = vec(x)
        x = tf.keras.layers.Embedding(vocab_size, embed_dim, name=f"emb_{tower_name}")(x)
        x = tf.keras.layers.SpatialDropout1D(0.15, name=f"sdrop_{tower_name}")(x)
        x = tf.keras.layers.GlobalAveragePooling1D(name=f"gap_{tower_name}")(x)
        x = tf.keras.layers.LayerNormalization(name=f"ln_{tower_name}")(x)
        return x

    t_main = text_tower(text_main_in, vec_main, "main")
    t_company = text_tower(text_company_in, vec_company, "company")
    t_context = text_tower(text_context_in, vec_context, "context")

    # Numeric input
    num_in = tf.keras.Input(shape=(num_dim,), dtype=tf.float32, name="num")
    n = tf.keras.layers.LayerNormalization(name="ln_num")(num_in)
    n = tf.keras.layers.Dense(32, activation="swish", name="num_dense1")(n)
    n = tf.keras.layers.Dropout(0.10, name="num_drop")(n)

    # Fusion
    x = tf.keras.layers.Concatenate(name="fusion")([t_main, t_company, t_context, n])
    x = tf.keras.layers.Dense(hidden, activation="swish", name="dense1")(x)
    x = tf.keras.layers.Dropout(0.20, name="drop1")(x)
    x = tf.keras.layers.Dense(hidden // 2, activation="swish", name="dense2")(x)
    out = tf.keras.layers.Dense(2, activation="linear", name="salary_out")(x)

    model = tf.keras.Model(
        inputs=[text_main_in, text_company_in, text_context_in, num_in],
        outputs=out,
        name="salary_predictor_multi_input",
    )
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=lr),
        loss=tf.keras.losses.Huber(delta=3.0),
        metrics=[tf.keras.metrics.MeanAbsoluteError(name="mae")],
    )

    vecs = {"main": vec_main, "company": vec_company, "context": vec_context}
    return model, vecs


def build_tf_model_use(
    *,
    use_url: str = "https://tfhub.dev/google/universal-sentence-encoder/4",
    num_dim: int = 2,
    hidden: int = 256,
    lr: float = 8e-4,
):
    """Build model using TF-Hub Universal Sentence Encoder for text."""
    _tf_env_guard()
    import tensorflow as tf

    try:
        import tensorflow_hub as hub  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "未检测到 tensorflow_hub。请安装 tensorflow-hub，或把 text_encoder 设置为 'avg_embed'。"
        ) from e

    text_main_in = tf.keras.Input(shape=(1,), dtype=tf.string, name="text_main")
    text_company_in = tf.keras.Input(shape=(1,), dtype=tf.string, name="text_company")
    text_context_in = tf.keras.Input(shape=(1,), dtype=tf.string, name="text_context")

    # USE expects rank-1 strings, so squeeze last dim
    use_layer = hub.KerasLayer(use_url, trainable=False, name="use")

    def use_tower(x, name: str):
        x = tf.squeeze(x, axis=1)
        x = use_layer(x)
        x = tf.keras.layers.LayerNormalization(name=f"ln_{name}")(x)
        return x

    t_main = use_tower(text_main_in, "main")
    t_company = use_tower(text_company_in, "company")
    t_context = use_tower(text_context_in, "context")

    num_in = tf.keras.Input(shape=(num_dim,), dtype=tf.float32, name="num")
    n = tf.keras.layers.LayerNormalization(name="ln_num")(num_in)
    n = tf.keras.layers.Dense(64, activation="swish", name="num_dense1")(n)
    n = tf.keras.layers.Dropout(0.10, name="num_drop")(n)

    x = tf.keras.layers.Concatenate(name="fusion")([t_main, t_company, t_context, n])
    x = tf.keras.layers.Dense(hidden, activation="swish", name="dense1")(x)
    x = tf.keras.layers.Dropout(0.25, name="drop1")(x)
    x = tf.keras.layers.Dense(hidden // 2, activation="swish", name="dense2")(x)
    # Predict log1p(K) for stability; invert in predict_salary()
    out = tf.keras.layers.Dense(2, activation="linear", name="salary_log_out")(x)

    model = tf.keras.Model(inputs=[text_main_in, text_company_in, text_context_in, num_in], outputs=out, name="salary_predictor_use")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=lr),
        loss=tf.keras.losses.Huber(delta=0.35),
        metrics=[tf.keras.metrics.MeanAbsoluteError(name="mae")],
    )
    return model, {}


def build_model_from_config(cfg: TrainConfig):
    """Factory that picks the text encoder."""
    if cfg.text_encoder.lower() == "use":
        try:
            return build_tf_model_use(num_dim=2, hidden=cfg.hidden, lr=cfg.lr)
        except Exception:
            # graceful fallback
            return build_tf_model(
                vocab_size=cfg.vocab_size,
                seq_len=cfg.seq_len,
                embed_dim=cfg.embed_dim,
                num_dim=2,
                hidden=cfg.hidden,
                lr=cfg.lr,
            )
    return build_tf_model(
        vocab_size=cfg.vocab_size,
        seq_len=cfg.seq_len,
        embed_dim=cfg.embed_dim,
        num_dim=2,
        hidden=cfg.hidden,
        lr=cfg.lr,
    )


def adapt_vectorizers(
    vectorizers: Dict[str, Any],
    texts: Dict[str, Sequence[str]],
    *,
    batch_size: int = 256,
):
    """Fit TextVectorization layers on your corpus.

    texts keys:
    - "main": list[str]  (title+desc)
    - "company": list[str] (company+industry)
    - "context": list[str] (city+work_years+edu)
    """

    import tensorflow as tf

    for k, vec in vectorizers.items():
        data = tf.data.Dataset.from_tensor_slices(_ensure_1d_str(texts.get(k, []))).batch(batch_size)
        vec.adapt(data)


def predict(
    model: Any,
    features: Union[SalaryFeatures, Dict[str, Any], Sequence[Union[SalaryFeatures, Dict[str, Any]]]],
) -> np.ndarray:
    """Run model inference. This is the function you can use for quick tests.

    Usage:
    - y = predict(model, SalaryFeatures(...))
    - y = predict(model, {"job_title": "...", ...})
    - y = predict(model, [SalaryFeatures(...), SalaryFeatures(...)])

    Returns:
    - np.ndarray with shape (batch, 2): [salary_min_k, salary_max_k]
    """

    import tensorflow as tf

    if isinstance(features, (SalaryFeatures, dict)):
        batch_in: List[Union[SalaryFeatures, Dict[str, Any]]] = [features]
    else:
        batch_in = list(features)

    batch: List[SalaryFeatures] = []
    for f in batch_in:
        if isinstance(f, SalaryFeatures):
            batch.append(f)
        else:
            batch.append(SalaryFeatures(**{**f}))  # type: ignore[arg-type]

    x = _as_np_batch(batch)
    # Keras expects shape (batch, 1) for string inputs in our graph
    feed = {
        "text_main": x["text_main"].reshape(-1, 1),
        "text_company": x["text_company"].reshape(-1, 1),
        "text_context": x["text_context"].reshape(-1, 1),
        "num": x["num"],
    }
    y = model(feed, training=False)
    return tf.convert_to_tensor(y).numpy()


def predict_salary_k(
    model: Any,
    features: Union[SalaryFeatures, Dict[str, Any], Sequence[Union[SalaryFeatures, Dict[str, Any]]]],
) -> np.ndarray:
    """Improved prediction logic.

    - Uses the same cleaning pipeline as training.
    - Supports models that output either K directly or log1p(K).
    - Enforces min<=max and clamps to a reasonable range.
    """
    y = predict(model, features)
    y = np.asarray(y, dtype=np.float32)

    # Heuristic: if output values are small (< ~6), treat as log1p(K)
    if np.nanmax(y) < 8.0:
        y = np.expm1(y)

    out = []
    for a, b in y.tolist():
        mn, mx = _ensure_min_max(float(a), float(b))
        out.append([mn, mx])
    return np.asarray(out, dtype=np.float32)


# -----------------------------
# Training: use our own Job data
# -----------------------------


def _setup_django(settings_module: str = "django_recruit.config.settings") -> None:
    """Initialize Django so this module can be used from CLI."""
    import os
    import sys

    # Ensure our Django project root is importable.
    # Layout: project/model/this_file.py  -> project/django_recruit/manage.py
    base = Path(__file__).resolve().parents[1] / "django_recruit"
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

    import django
    from django.apps import apps

    if not apps.ready:
        django.setup()


def load_features_from_django_jobs(
    *,
    settings_module: str = "config.settings",
    limit: Optional[int] = None,
) -> Tuple[List[SalaryFeatures], np.ndarray]:
    """Load training pairs (X features, y targets) from our Django Job tables."""
    _setup_django(settings_module=settings_module)

    from django.db.models import Q

    from job.models import Job  # type: ignore

    qs = (
        Job.objects.select_related("company")
        .filter(Q(job_title__isnull=False) & ~Q(job_title=""))
        .order_by("-updated_at")
    )
    if limit:
        qs = qs[: int(limit)]

    X: List[SalaryFeatures] = []
    y_rows: List[List[float]] = []

    for j in qs:
        co = getattr(j, "company", None)

        title = clean_text(j.job_title, max_len=120)
        desc = clean_text(j.job_j, max_len=2600)
        company = clean_text(getattr(co, "comp_compName", "") if co else "", max_len=80)
        industry = clean_text(getattr(co, "comp_compIndustry", "") if co else "", max_len=80)
        city = clean_text(j.query_city_name or j.job_dq or "", max_len=40)
        work_years = clean_text(j.job_requireWorkYears or "", max_len=40)
        edu = clean_text(j.job_requireEduLevel or "", max_len=20)

        # labels: prefer structured fields; fallback to parsing salary text
        min_k = j.salary_min
        max_k = j.salary_max
        if min_k is None and max_k is None:
            a, b = parse_salary_to_k(j.job_salary)
            min_k = a
            max_k = b
        if min_k is None and max_k is None:
            continue
        mn, mx = _ensure_min_max(_safe_float(min_k), _safe_float(max_k))
        if mn <= 0.0 and mx <= 0.0:
            continue

        X.append(
            SalaryFeatures(
                job_title=title,
                job_desc=desc,
                company=company,
                industry=industry,
                city=city,
                work_years=work_years,
                edu=edu,
                salary_min_k=None,
                salary_max_k=None,
            )
        )
        y_rows.append([mn, mx])

    y = np.asarray(y_rows, dtype=np.float32)
    return X, y


def _train_val_split(n: int, val_ratio: float, seed: int) -> Tuple[np.ndarray, np.ndarray]:
    idx = np.arange(n)
    rng = np.random.default_rng(seed)
    rng.shuffle(idx)
    v = int(max(1, round(n * val_ratio)))
    val_idx = idx[:v]
    tr_idx = idx[v:]
    return tr_idx, val_idx


def _batch_feed(X: Sequence[SalaryFeatures], idx: np.ndarray) -> Dict[str, np.ndarray]:
    batch = [X[i] for i in idx.tolist()]
    x = _as_np_batch(batch)
    return {
        "text_main": x["text_main"].reshape(-1, 1),
        "text_company": x["text_company"].reshape(-1, 1),
        "text_context": x["text_context"].reshape(-1, 1),
        "num": x["num"],
    }


def train_from_django(
    *,
    cfg: Optional[TrainConfig] = None,
    settings_module: str = "config.settings",
) -> Dict[str, Any]:
    """Train model using our own Job data and save artifacts.

    Returns a dict with keys: out_dir, history, n_train, n_val
    """
    _tf_env_guard()
    import tensorflow as tf

    cfg = cfg or TrainConfig()
    X, y_k = load_features_from_django_jobs(settings_module=settings_module, limit=cfg.limit)

    if len(X) < cfg.min_samples:
        raise RuntimeError(f"可用于训练的数据太少：{len(X)}，请先导入更多岗位数据或降低 min_samples。")

    print(f"[salary_train] loaded samples: {len(X)} (limit={cfg.limit})")

    # target engineering: log1p(K) for stability
    y_k = np.asarray(y_k, dtype=np.float32)
    y_log = np.log1p(np.clip(y_k, 0.0, 300.0))

    tr_idx, val_idx = _train_val_split(len(X), cfg.val_ratio, cfg.seed)
    print(f"[salary_train] split: train={len(tr_idx)} val={len(val_idx)} val_ratio={cfg.val_ratio}")

    model, vecs = build_model_from_config(cfg)
    print(f"[salary_train] model: {model.name} text_encoder={cfg.text_encoder}")

    # If using avg_embed towers, adapt vectorizers on training text
    if vecs:
        texts = _as_np_batch([X[i] for i in tr_idx.tolist()])
        adapt_vectorizers(
            vecs,
            {
                "main": texts["text_main"].tolist(),
                "company": texts["text_company"].tolist(),
                "context": texts["text_context"].tolist(),
            },
        )

    # Build tf.data
    def make_ds(idxs: np.ndarray, shuffle: bool) -> tf.data.Dataset:
        x = _batch_feed(X, idxs)
        y = y_log[idxs]
        ds = tf.data.Dataset.from_tensor_slices((x, y))
        if shuffle:
            ds = ds.shuffle(min(len(idxs), 20000), seed=cfg.seed, reshuffle_each_iteration=True)
        ds = ds.batch(cfg.batch_size).prefetch(tf.data.AUTOTUNE)
        return ds

    ds_tr = make_ds(tr_idx, shuffle=True)
    ds_val = make_ds(val_idx, shuffle=False)

    callbacks: List[Any] = [
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=cfg.patience, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.6, patience=max(1, cfg.patience // 2), min_lr=1e-5),
    ]

    hist = model.fit(ds_tr, validation_data=ds_val, epochs=cfg.epochs, callbacks=callbacks, verbose=cfg.verbose)

    out_dir = Path(cfg.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[salary_train] saving to: {out_dir.resolve()}")

    # Save model (SavedModel)
    model.save(str(out_dir / "saved_model"))

    # Save config & a tiny report
    report = {
        "n_total": int(len(X)),
        "n_train": int(len(tr_idx)),
        "n_val": int(len(val_idx)),
        "text_encoder": cfg.text_encoder,
        "metrics": {k: [float(x) for x in v] for k, v in hist.history.items()},
    }
    (out_dir / "train_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "train_config.json").write_text(json.dumps(cfg.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[salary_train] done.")
    return {"out_dir": str(out_dir), "history": hist.history, "n_train": int(len(tr_idx)), "n_val": int(len(val_idx))}


def save_model(model: Any, out_dir: Union[str, Path]) -> str:
    """Save a TF SavedModel directory."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    model.save(str(out_dir))
    return str(out_dir)


def load_model(model_dir: Union[str, Path]) -> Any:
    """Load a TF SavedModel directory."""
    import tensorflow as tf

    return tf.keras.models.load_model(str(model_dir))

