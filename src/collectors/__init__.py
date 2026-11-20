from src.collectors import arbeitnow, remotive

# Registry of available sources: name -> fetch function
COLLECTORS = {
    "arbeitnow": arbeitnow.fetch_jobs,
    "remotive": remotive.fetch_jobs,
}
