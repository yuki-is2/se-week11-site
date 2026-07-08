from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session, flash
)
from database import SessionLocal
from models.ootd_log import OotdLog
from config import SEASONS, MEMO_MAX_LENGTH
from datetime import date

ootd_bp = Blueprint("ootd", __name__, url_prefix="/ootd")

WEATHER_OPTIONS = ["晴", "曇", "雨", "雪"]

# ───────────────────────────────
# OOTD登録画面（C-07対応）
# ───────────────────────────────
@ootd_bp.route("/register", methods=["GET", "POST"])
def register():
    result_path = session.get("coord_result")
    clothing_ids = session.get("coord_clothing_ids", [])

    if not result_path:
        flash("先にコーディネートを作成してください。", "error")
        return redirect(url_for("clothing.coordinate"))

    if request.method == "GET":
        return render_template(
            "ootd/register.html",
            result_path=result_path,
            seasons=SEASONS,
            weather_options=WEATHER_OPTIONS,
            today=date.today().strftime("%Y-%m-%d"),
        )

    # 入力値を取得
    memo = request.form.get("memo", "").strip()
    weather = request.form.get("weather", "").strip()
    season = request.form.get("season", "").strip()

    # バリデーション（NF-U04対応）
    errors = []
    if len(memo) > MEMO_MAX_LENGTH:
        errors.append(f"メモは{MEMO_MAX_LENGTH}文字以内で入力してください。")
    if weather and weather not in WEATHER_OPTIONS:
        errors.append("天気を正しく選択してください。")
    if season and season not in SEASONS:
        errors.append("季節を正しく選択してください。")

    if errors:
        for e in errors:
            flash(e, "error")
        return render_template(
            "ootd/register.html",
            result_path=result_path,
            seasons=SEASONS,
            weather_options=WEATHER_OPTIONS,
            today=date.today().strftime("%Y-%m-%d"),
        )

    # DBに保存
    import json
    db = SessionLocal()
    try:
        ootd = OotdLog(
            date=date.today(),
            weather=weather or None,
            season=season or None,
            memo=memo or None,
            snapshot_path=result_path,
            clothing_ids=json.dumps(clothing_ids),
        )
        db.add(ootd)
        db.commit()

        # セッションをクリア
        session.pop("coord_result", None)
        session.pop("coord_clothing_ids", None)

        flash("今日のOOTDを登録しました！", "success")
        return redirect(url_for("ootd.gallery"))
    except Exception:
        db.rollback()
        flash("保存中にエラーが発生しました。もう一度お試しください。", "error")
        return redirect(url_for("ootd.register"))
    finally:
        db.close()


# ───────────────────────────────
# OOTDギャラリー（S-06対応）
# ───────────────────────────────
@ootd_bp.route("/gallery")
def gallery():
    db = SessionLocal()
    try:
        logs = db.query(OotdLog).order_by(OotdLog.date.desc()).all()
        logs_data = [l.to_dict() for l in logs]
    finally:
        db.close()

    return render_template("ootd/gallery.html", logs=logs_data)


# ───────────────────────────────
# OOTD削除（S-11対応）
# ───────────────────────────────
@ootd_bp.route("/delete/<int:log_id>", methods=["POST"])
def delete(log_id):
    db = SessionLocal()
    try:
        log = db.query(OotdLog).filter(OotdLog.id == log_id).first()
        if not log:
            flash("指定したOOTDが見つかりませんでした。", "error")
            return redirect(url_for("ootd.gallery"))

        db.delete(log)
        db.commit()
        flash("OOTDを削除しました。", "success")
    except Exception:
        db.rollback()
        flash("削除中にエラーが発生しました。", "error")
    finally:
        db.close()

    return redirect(url_for("ootd.gallery"))