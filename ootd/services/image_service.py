import uuid
from pathlib import Path
from PIL import Image
import rembg
from config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH

class ImageServiceError(Exception):
    """画像処理サービス独自の例外（NF-U04対応）"""
    pass

def allowed_file(filename: str) -> bool:
    """拡張子チェック（NF-S02対応）"""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )

def validate_image(file) -> None:
    """ファイルサイズ・形式を検証する（NF-S02, NF-P04対応）"""
    file.seek(0, 2)  # ファイル末尾へ
    size = file.tell()
    file.seek(0)     # 先頭に戻す

    if size > MAX_CONTENT_LENGTH:
        raise ImageServiceError(
            f"ファイルサイズが上限（10MB）を超えています（{size // 1024 // 1024}MB）"
        )

def remove_background(file) -> Path:
    """
    背景を除去して透過PNGを保存する（C-02対応）
    戻り値: 保存したファイルのパス（static/uploads/配下の相対パス）
    """
    validate_image(file)

    # 元画像をPillowで読み込む
    try:
        input_image = Image.open(file).convert("RGBA")
    except Exception:
        raise ImageServiceError("画像ファイルの読み込みに失敗しました。別の画像をお試しください。")

    # rembgで背景除去（NF-P01: 10秒以内が目標）
    try:
        output_image = rembg.remove(input_image)
    except Exception:
        raise ImageServiceError("背景の除去処理に失敗しました。もう一度お試しください。")

    # ユニークなファイル名で保存（NF-S03: パス操作対策）
    filename = f"{uuid.uuid4().hex}.png"
    save_path = UPLOAD_FOLDER / filename

    output_image.save(save_path, format="PNG")

    # テンプレートから参照できる相対パスを返す
    return Path("uploads") / filename