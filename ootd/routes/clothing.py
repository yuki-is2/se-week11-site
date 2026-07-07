from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session, flash
)
from services.image_service import remove_background, allowed_file, ImageServiceError
from database import SessionLocal
from models.clothing import Clothing
from config import CATEGORIES, SEASONS, MEMO_MAX_LENGTH

clothing_bp = Blueprint("clothing", __name__, url_prefix="/clothing")

# ───────────────────────────────
# 服の登録 Step1: 画像アップロード
# ───────────────────────────────
@clothing_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("clothing/register.html")

    # ファイル存在チェック（NF-U04対応）
    if "image" not in request.files or request.files["image"].filename == "":
        flash("画像を選択してください。", "error")
        return render_template("clothing/register.html")

    file = request.files["image"]

    if not allowed_file(file.filename):
        flash("対応していないファイル形式です（jpg / png / heic）。", "error")
        return render_template("clothing/register.html")

    # 背景除去処理（C-02対応）
    try:
        relative_path = remove_background(file)
    except ImageServiceError as e:
        flash(str(e), "error")
        return render_template("clothing/register.html")

    # プレビュー用に一時保存（sessionに画像パスを保持）
    session["preview_image"] = str(relative_path).replace("\\", "/")
    return redirect(url_for("clothing.preview"))


# ───────────────────────────────
# 服の登録 Step2: プレビュー確認
# ───────────────────────────────
@clothing_bp.route("/preview", methods=["GET", "POST"])
def preview():
    image_path = session.get("preview_image")
    if not image_path:
        flash("先に画像をアップロードしてください。", "error")
        return redirect(url_for("clothing.register"))

    if request.method == "GET":
        return render_template(
            "clothing/preview.html",
            image_path=image_path,
            categories=CATEGORIES,
            seasons=SEASONS,
        )

    # Step3: メタ情報入力 + DB保存（C-03対応）
    category = request.form.get("category", "").strip()
    season = request.form.get("season", "").strip()

    # 入力バリデーション（NF-U04対応）
    errors = []
    if category not in CATEGORIES:
        errors.append("カテゴリを正しく選択してください。")
    if season not in SEASONS:
        errors.append("季節を正しく選択してください。")

    if errors:
        for e in errors:
            flash(e, "error")
        return render_template(
            "clothing/preview.html",
            image_path=image_path,
            categories=CATEGORIES,
            seasons=SEASONS,
        )

    # DBに保存
    db = SessionLocal()
    try:
        clothing = Clothing(
            category=category,
            season=season,
            image_path=image_path,
        )
        db.add(clothing)
        db.commit()
        session.pop("preview_image", None)
        flash("服を登録しました！", "success")
        return redirect(url_for("index"))
    except Exception:
        db.rollback()
        flash("保存中にエラーが発生しました。もう一度お試しください。", "error")
        return render_template(
            "clothing/preview.html",
            image_path=image_path,
            categories=CATEGORIES,
            seasons=SEASONS,
        )
    finally:
        db.close()

# ───────────────────────────────
# クローゼット一覧（S-01, S-02対応）
# ───────────────────────────────
@clothing_bp.route("/closet")
def closet():
    category = request.args.get("category", "")
    season = request.args.get("season", "")

    db = SessionLocal()
    try:
        query = db.query(Clothing)

        # フィルタ適用（S-02対応）
        if category:
            query = query.filter(Clothing.category == category)
        if season:
            query = query.filter(Clothing.season == season)

        clothes = query.order_by(Clothing.created_at.desc()).all()
    finally:
        db.close()

    return render_template(
        "clothing/closet.html",
        clothes=clothes,
        categories=CATEGORIES,
        seasons=SEASONS,
        selected_category=category,
        selected_season=season,
    )


# ───────────────────────────────
# 服の削除（S-04対応）
# ───────────────────────────────
@clothing_bp.route("/delete/<int:clothing_id>", methods=["POST"])
def delete(clothing_id):
    db = SessionLocal()
    try:
        clothing = db.query(Clothing).filter(Clothing.id == clothing_id).first()

        if not clothing:
            flash("指定した服が見つかりませんでした。", "error")
            return redirect(url_for("clothing.closet"))

        # 画像ファイルも削除（I-01対応）
        from config import UPLOAD_FOLDER
        image_file = UPLOAD_FOLDER / clothing.image_path.split("uploads/")[-1]
        if image_file.exists():
            image_file.unlink()

        db.delete(clothing)
        db.commit()
        flash("服を削除しました。", "success")
    except Exception:
        db.rollback()
        flash("削除中にエラーが発生しました。", "error")
    finally:
        db.close()

    return redirect(url_for("clothing.closet"))