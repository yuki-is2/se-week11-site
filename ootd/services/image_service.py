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

def composite_on_mannequin(clothing_paths: list, mannequin_path: Path, categories: list = None) -> str:
    """
    マネキン画像に複数の服を重ねて合成する（C-04, C-06対応）
    カテゴリに応じて配置位置・サイズを調整する
    """
    if not mannequin_path.exists():
        raise ImageServiceError("マネキン画像が見つかりません。static/mannequin.png を確認してください。")

    base = Image.open(mannequin_path).convert("RGBA")
    base_w, base_h = base.size  # 300 x 600

    # カテゴリごとの配置設定（位置・サイズ）
    LAYOUT = LAYOUT = {
        "トップス":     {"x": 0.32, "y": 0.16, "w": 0.45, "h": 0.35},
        "アウター":     {"x": 0.05, "y": 0.16, "w": 0.90, "h": 0.45},
        "ボトムス":     {"x": 0.20, "y": 0.45, "w": 0.70, "h": 0.42},
        "ワンピース":   {"x": 0.10, "y": 0.18, "w": 0.80, "h": 0.75},
        "シューズ":     {"x": 0.20, "y": 0.85, "w": 0.60, "h": 0.12},
        "バッグ":       {"x": 0.60, "y": 0.42, "w": 0.35, "h": 0.25},
        "アクセサリー": {"x": 0.35, "y": 0.03, "w": 0.30, "h": 0.10},
    }
    DEFAULT_LAYOUT = {"x": 0.10, "y": 0.22, "w": 0.80, "h": 0.38}

    for i, rel_path in enumerate(clothing_paths):
        clothing_file = UPLOAD_FOLDER / rel_path.split("uploads/")[-1]
        if not clothing_file.exists():
            continue

        # カテゴリに応じたレイアウトを取得
        category = categories[i] if categories and i < len(categories) else None
        layout = LAYOUT.get(category, DEFAULT_LAYOUT)

        # 配置サイズを計算
        paste_w = int(base_w * layout["w"])
        paste_h = int(base_h * layout["h"])
        paste_x = int(base_w * layout["x"])
        paste_y = int(base_h * layout["y"])

        # 服の画像をリサイズ
        clothing_img = Image.open(clothing_file).convert("RGBA")
        clothing_img = clothing_img.resize((paste_w, paste_h), Image.LANCZOS)

        # 透明レイヤーに貼り付けて合成
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        layer.paste(clothing_img, (paste_x, paste_y))
        base = Image.alpha_composite(base, layer)

    # 合成結果を保存
    filename = f"coord_{uuid.uuid4().hex}.png"
    save_path = UPLOAD_FOLDER / filename
    base.save(save_path, format="PNG")

    return str(Path("uploads") / filename).replace("\\", "/")