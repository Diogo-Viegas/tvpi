from tmdb import search_tv_show
from flask import Flask, render_template, request, redirect, url_for
from database import get_db, init_db
from tmdb import get_season_episodes

app = Flask(__name__)

@app.route("/")
def index():
    search = request.args.get("search", "")
    status = request.args.get("status", "")

    query = """
            SELECT
                series.*,
                COUNT(episodes.id) AS total_episodes,
                SUM(CASE WHEN episodes.watched = 1 THEN 1 ELSE 0 END) AS watched_episodes
            FROM series
            LEFT JOIN episodes ON episodes.series_id = series.id
            WHERE 1=1
    """
    params = []

    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")

    if status:
        query += " AND status = ?"
        params.append(status)

    query += " GROUP BY series.id ORDER BY series.created_at DESC"

    db = get_db()
    series = db.execute(query, params).fetchall()
    db.close()

    return render_template(
        "index.html",
        series=series,
        search=search,
        status=status
    )

@app.route("/add", methods=["GET", "POST"])
def add_series():
    if request.method == "POST":
        title = request.form["title"]
        status = request.form["status"]
        rating = request.form.get("rating") or None

        tmdb_data = search_tv_show(title)

        if tmdb_data:
            title = tmdb_data["title"] or title
            poster_url = tmdb_data["poster_url"]
            tmdb_id = tmdb_data["tmdb_id"]
            overview = tmdb_data["overview"]
            first_air_date = tmdb_data["first_air_date"]
        else:
            poster_url = request.form.get("poster_url") or None
            tmdb_id = None
            overview = None
            first_air_date = None

        db = get_db()
        db.execute(
            """
            INSERT INTO series
            (title, status, rating, poster_url, tmdb_id, overview, first_air_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (title, status, rating, poster_url, tmdb_id, overview, first_air_date)
        )
        db.commit()
        db.close()

        return redirect(url_for("index"))

    return render_template("add_series.html")

@app.route("/init-db")
def init_database():
    init_db()
    return "Base de dados criada com sucesso!"


@app.route("/series/<int:series_id>")
def series_detail(series_id):
    db = get_db()

    show = db.execute(
        "SELECT * FROM series WHERE id = ?",
        (series_id,)
    ).fetchone()

    if show is None:
        db.close()
        return "Série não encontrada", 404

    episodes = db.execute(
        """
        SELECT *
        FROM episodes
        WHERE series_id = ?
        ORDER BY season ASC, episode ASC
        """,
        (series_id,)
        ).fetchall()
    total = len(episodes)
    watched = sum(1 for ep in episodes if ep["watched"])
    progress = int((watched / total) * 100) if total > 0 else 0

    next_episode = None
    for ep in episodes:
        if not ep["watched"]:
            next_episode = ep
            break

    db.close()

    return render_template(
        "series_detail.html",
        show=show,
        episodes=episodes,
        total=total,
        watched=watched,
        progress=progress,
        next_episode=next_episode
    )

@app.route("/series/<int:series_id>/edit", methods=["GET", "POST"])
def edit_series(series_id):
    db = get_db()
    show = db.execute(
        "SELECT * FROM series WHERE id = ?",
        (series_id,)
    ).fetchone()

    if show is None:
        db.close()
        return "Série não encontrada", 404

    if request.method == "POST":
        title = request.form["title"]
        status = request.form["status"]
        rating = request.form.get("rating") or None
        poster_url = request.form.get("poster_url") or None

        db.execute(
            """
            UPDATE series
            SET title = ?, status = ?, rating = ?, poster_url = ?
            WHERE id = ?
            """,
            (title, status, rating, poster_url, series_id)
        )
        db.commit()
        db.close()

        return redirect(url_for("series_detail", series_id=series_id))

    db.close()
    return render_template("edit_series.html", show=show)


@app.route("/series/<int:series_id>/delete", methods=["POST"])
def delete_series(series_id):
    db = get_db()
    db.execute(
        "DELETE FROM series WHERE id = ?",
        (series_id,)
    )
    db.commit()
    db.close()

    return redirect(url_for("index"))

@app.route("/series/<int:series_id>/episodes/add", methods=["POST"])
def add_episode(series_id):
    season = request.form["season"]
    episode = request.form["episode"]
    title = request.form.get("title") or None

    db = get_db()
    db.execute(
        """
        INSERT INTO episodes (series_id, season, episode, title)
        VALUES (?, ?, ?, ?)
        """,
        (series_id, season, episode, title)
    )
    db.commit()
    db.close()

    return redirect(url_for("series_detail", series_id=series_id))


@app.route("/episodes/<int:episode_id>/toggle", methods=["POST"])
def toggle_episode(episode_id):
    db = get_db()

    ep = db.execute(
        "SELECT * FROM episodes WHERE id = ?",
        (episode_id,)
    ).fetchone()

    if ep is None:
        db.close()
        return "Episódio não encontrado", 404

    new_status = 0 if ep["watched"] else 1

    db.execute(
        """
        UPDATE episodes
        SET watched = ?,
            watched_at = CASE WHEN ? = 1 THEN CURRENT_TIMESTAMP ELSE NULL END
        WHERE id = ?
        """,
        (new_status, new_status, episode_id)
    )

    db.commit()
    series_id = ep["series_id"]
    db.close()

    return redirect(url_for("series_detail", series_id=series_id))


@app.route("/episodes/<int:episode_id>/delete", methods=["POST"])
def delete_episode(episode_id):
    db = get_db()

    ep = db.execute(
        "SELECT * FROM episodes WHERE id = ?",
        (episode_id,)
    ).fetchone()

    if ep is None:
        db.close()
        return "Episódio não encontrado", 404

    series_id = ep["series_id"]

    db.execute(
        "DELETE FROM episodes WHERE id = ?",
        (episode_id,)
    )

    db.commit()
    db.close()

    return redirect(url_for("series_detail", series_id=series_id))   

@app.route("/series/<int:series_id>/import-season", methods=["POST"])
def import_season(series_id):
    season_number = int(request.form["season"])

    db = get_db()

    show = db.execute(
        "SELECT * FROM series WHERE id = ?",
        (series_id,)
    ).fetchone()

    if not show or not show["tmdb_id"]:
        db.close()
        return "Série sem ligação TMDB", 400

    episodes = get_season_episodes(show["tmdb_id"], season_number)

    for ep in episodes:
        db.execute(
            """
            INSERT OR IGNORE INTO episodes (series_id, season, episode, title)
            VALUES (?, ?, ?, ?)
            """,
            (series_id, ep["season"], ep["episode"], ep["title"])
        )

    db.commit()
    db.close()

    return redirect(url_for("series_detail", series_id=series_id))

@app.route("/continue")
def continue_watching():
    db = get_db()

    shows = db.execute(
        """
        SELECT
            series.id,
            series.title,
            series.poster_url,
            episodes.id AS episode_id,
            episodes.season,
            episodes.episode,
            episodes.title AS episode_title
        FROM series
        JOIN episodes ON episodes.series_id = series.id
        WHERE episodes.watched = 0
        AND episodes.id = (
            SELECT e2.id
            FROM episodes e2
            WHERE e2.series_id = series.id
            AND e2.watched = 0
            ORDER BY e2.season ASC, e2.episode ASC
            LIMIT 1
        )
        ORDER BY series.title ASC
        """
    ).fetchall()

    db.close()

    return render_template("continue.html", shows=shows)


@app.route("/history")
def history():
    db = get_db()

    episodes = db.execute(
        """
        SELECT
            series.id AS series_id,
            series.title AS series_title,
            series.poster_url,
            episodes.season,
            episodes.episode,
            episodes.title AS episode_title,
            episodes.watched_at
        FROM episodes
        JOIN series ON series.id = episodes.series_id
        WHERE episodes.watched = 1
        ORDER BY episodes.watched_at DESC
        LIMIT 50
        """
    ).fetchall()

    db.close()

    return render_template("history.html", episodes=episodes)

@app.route("/series/<int:series_id>/favorite", methods=["POST"])
def toggle_favorite(series_id):
    db = get_db()

    show = db.execute(
        "SELECT favorite FROM series WHERE id = ?",
        (series_id,)
    ).fetchone()

    if show is None:
        db.close()
        return "Série não encontrada", 404

    new_value = 0 if show["favorite"] else 1

    db.execute(
        "UPDATE series SET favorite = ? WHERE id = ?",
        (new_value, series_id)
    )

    db.commit()
    db.close()

    return redirect(url_for("series_detail", series_id=series_id))
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)