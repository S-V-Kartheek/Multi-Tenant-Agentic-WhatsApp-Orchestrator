"""
db/repositories — Repository layer exposing all data access modules.

Each module owns one MongoDB collection. Importing from this package keeps
the rest of the app decoupled from raw Motor queries.
"""
from . import tenant_repo, session_repo, message_repo, agent_run_repo, campaign_repo

__all__ = [
    "tenant_repo",
    "session_repo",
    "message_repo",
    "agent_run_repo",
    "campaign_repo",
]
