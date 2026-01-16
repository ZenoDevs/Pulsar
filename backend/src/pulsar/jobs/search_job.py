from typing import Optional

from ..core.state import jobs, clusters_cache
from ..domain import Article
from ..core.clustering import cluster_articles
from ..infrastructure.scrapers.news_scrapers import fetch_articles_from_all_sources, SOURCE_NAMES, SOURCE_BIAS
from ..db.orm import search_articles_in_db, get_latest_article_date, save_article, SessionLocal

def process_search_job(job_id: str, query: str, start_date: Optional[str], end_date: Optional[str]):
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["message"] = "Searching database and external sources..."

        with SessionLocal() as db:
            local_results = search_articles_in_db(db, query, start_date, end_date)
            local_articles: list[Article] = []

            for r in local_results:
                try:
                    save_article(db, r, query=query)

                    s_id = r["source_id"]
                    s_name = SOURCE_NAMES.get(s_id, s_id)
                    bias = r["bias"] if r["bias"] else SOURCE_BIAS.get(s_id, "unknown")

                    local_articles.append(
                        Article(
                            id=r["id"],
                            source_id=s_id,
                            source_name=s_name,
                            bias=bias,
                            bias_source=SOURCE_BIAS.get(s_id, "unknown"),
                            bias_article=r["bias_article"],
                            bias_confidence=r["bias_confidence"],
                            bias_explanation=r["bias_explanation"],
                            title=r["title"],
                            snippet=r["snippet"] or "",
                            body=r["body"],
                            url=r["url"],
                            published_at=r["published_at"],
                            embedding=r["embedding"],
                        )
                    )
                except Exception as ex:
                    print(f"Error reconstructing article from DB: {ex}")
                    continue

            scrape_start_date = start_date
            scrape_max_pages = 2
            cutoff_date = None

            if not start_date and not end_date:
                last_db_date = get_latest_article_date(db, query)
                if last_db_date:
                    cutoff_date = last_db_date
                    scrape_start_date = last_db_date.strftime("%Y-%m-%d")

            live_articles = fetch_articles_from_all_sources(
                query=query,
                start_date=scrape_start_date,
                end_date=end_date,
                max_pages=scrape_max_pages,
                cutoff_date=cutoff_date,
            )

            merged_map = {a.url: a for a in local_articles if a.url}
            for a in live_articles:
                if a.url:
                    merged_map[a.url] = a

            all_articles = list(merged_map.values())

            jobs[job_id]["message"] = f"Clustering {len(all_articles)} articles..."
            clusters = cluster_articles(query, all_articles)

            for cluster in clusters:
                clusters_cache[cluster.id] = cluster

            jobs[job_id]["clusters"] = clusters
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["message"] = "Done"

    except Exception as e:
        print(f"Job {job_id} failed: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = str(e)
