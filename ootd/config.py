import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# アップロード設定（NF-P04: 最大10MB）
MAX_CONTENT_LENGTH = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "heic"}

# 保存先
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# DB
DATABASE_URL = f"sqlite:///{BASE_DIR / 'ootd.db'}"

# メモ文字数上限（S-08対応）
MEMO_MAX_LENGTH = 200

# カテゴリ選択肢
CATEGORIES = ["トップス", "ボトムス", "アウター", "ワンピース",
              "シューズ", "バッグ", "アクセサリー"]

# 季節選択肢
SEASONS = ["春", "夏", "秋", "冬", "オールシーズン"]