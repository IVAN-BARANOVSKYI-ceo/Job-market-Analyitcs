import argparse
import logging
import sys

import config
from src.analysis.report import build_summary
from src.collectors import COLLECTORS
from src.collectors.raw_store import load_latest_raw, save_raw
from src.database import db
from src.processing.pipeline import process_jobs
from src.processing.standardize import standardize_source
from src.visualization.charts import build_all

logger = logging.getLogger("pipeline")


# Parse command line arguments
def parse_args():
    parser = argparse.ArgumentParser(description="Job Market Intelligence pipeline")
    parser.add_argument("--sources", nargs="+", default=list(COLLECTORS), choices=list(COLLECTORS),
                        help="Sources to use (default: all)")
    parser.add_argument("--skip-collect", action="store_true",
                        help="Do not call APIs, reuse the latest raw file of each source")
    parser.add_argument("--skip-analysis", action="store_true",
                        help="Only collect, process and store data")
    return parser.parse_args()


# Get raw jobs per source; a failing source is skipped, the others continue
def collect(sources, skip_collect):
    raw_by_source = {}
    for name in sources:
        try:
            if skip_collect:
                raw_jobs = load_latest_raw(name)
                logger.info("%s: loaded %s raw jobs from the latest file", name, len(raw_jobs))
            else:
                raw_jobs = COLLECTORS[name]()
                path = save_raw(name, raw_jobs)
                logger.info("%s: collected %s jobs, saved to %s", name, len(raw_jobs), path.name)
            raw_by_source[name] = raw_jobs
        except Exception as exc:
            logger.error("%s: failed and was skipped (%s)", name, exc)
    return raw_by_source


# Run the whole pipeline
def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()

    raw_by_source = collect(args.sources, args.skip_collect)
    records = []
    for name, raw_jobs in raw_by_source.items():
        records.extend(standardize_source(name, raw_jobs))
    if not records:
        logger.error("No data collected from any source")
        return 1

    jobs, stats = process_jobs(records)
    logger.info("Processing steps: %s", stats)

    conn = db.connect()
    inserted, updated = db.load_jobs(conn, jobs)
    logger.info("Database: %s new jobs, %s updated jobs", inserted, updated)

    if not args.skip_analysis:
        figures = build_all(conn)
        logger.info("Saved %s figures to %s", len(figures), config.FIGURES_DIR)
        summary = build_summary(conn, stats, figures)
        config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        (config.REPORTS_DIR / "summary.md").write_text(summary, encoding="utf-8")
        logger.info("Summary written to reports/summary.md")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
