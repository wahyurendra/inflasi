"""Firebase Admin init + ID-token verification.

The api-gateway is the single verifier of Firebase ID tokens — both the web app and
the future Android app send tokens minted by Firebase Auth, and this verifies them.

Credentials (first match wins):
  FIREBASE_CREDENTIALS_FILE  — path to a service-account JSON
  GOOGLE_APPLICATION_CREDENTIALS / workload identity  — Application Default Credentials
"""

import os
import threading

import firebase_admin
from firebase_admin import auth as fb_auth, credentials

_lock = threading.Lock()


def _ensure_app() -> None:
    if firebase_admin._apps:
        return
    with _lock:
        if firebase_admin._apps:
            return
        cred_file = os.getenv("FIREBASE_CREDENTIALS_FILE")
        if cred_file and os.path.exists(cred_file):
            firebase_admin.initialize_app(credentials.Certificate(cred_file))
        else:
            # Application Default Credentials (GOOGLE_APPLICATION_CREDENTIALS, or
            # GKE/Cloud Run workload identity). project_id may be required via env.
            firebase_admin.initialize_app()


def verify_id_token(id_token: str) -> dict:
    """Verify a Firebase ID token; returns the decoded claims. Raises on invalid."""
    _ensure_app()
    return fb_auth.verify_id_token(id_token)
