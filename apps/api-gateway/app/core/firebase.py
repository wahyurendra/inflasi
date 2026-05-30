"""Firebase Admin init + ID-token verification.

The api-gateway is the single verifier of Firebase ID tokens — both the web app and
the future Android app send tokens minted by Firebase Auth, and this verifies them.

Credentials (first match wins):
  FIREBASE_CREDENTIALS_FILE  — path to a service-account JSON
  GOOGLE_APPLICATION_CREDENTIALS / workload identity  — Application Default Credentials
"""

import logging
import os
import threading

import firebase_admin
from firebase_admin import auth as fb_auth, credentials

from app.config import settings

logger = logging.getLogger("inflasi-api")

_lock = threading.Lock()


def _ensure_app() -> None:
    if firebase_admin._apps:
        return
    with _lock:
        if firebase_admin._apps:
            return
        # settings.firebase_credentials_file comes from .env via pydantic; os.getenv
        # is only a fallback for environments that inject it into os.environ directly
        # (e.g. Docker --env-file, K8s secret env).
        cred_file = settings.firebase_credentials_file or os.getenv("FIREBASE_CREDENTIALS_FILE")
        if cred_file and os.path.exists(cred_file):
            logger.info("Firebase Admin: using service-account file %s", cred_file)
            firebase_admin.initialize_app(credentials.Certificate(cred_file))
        else:
            logger.warning(
                "Firebase Admin: FIREBASE_CREDENTIALS_FILE not set or missing (%r); "
                "falling back to Application Default Credentials. ID-token verification "
                "will fail if ADC has no project.",
                cred_file,
            )
            # Application Default Credentials (GOOGLE_APPLICATION_CREDENTIALS, or
            # GKE/Cloud Run workload identity). project_id may be required via env.
            firebase_admin.initialize_app()


def verify_id_token(id_token: str) -> dict:
    """Verify a Firebase ID token; returns the decoded claims. Raises on invalid."""
    _ensure_app()
    return fb_auth.verify_id_token(id_token)
