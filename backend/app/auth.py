import os
import jwt
from jwt.algorithms import RSAAlgorithm
import requests
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

# Configuration
CLERK_PEM_PUBLIC_KEY = os.getenv("CLERK_PEM_PUBLIC_KEY") # Optional: Static key
CLERK_ISSUER_URL = os.getenv("CLERK_ISSUER_URL") # e.g. https://clerk.your-site.com
CLERK_API_KEY = os.getenv("CLERK_SECRET_KEY")

security = HTTPBearer()

# Simple localized cache for JWKS
jwks_cache: Dict[str, Any] = {}
jwks_cache_expiry: Optional[datetime] = None

def get_jwks() -> dict:
    """Fetch and cache JWKS keys from Clerk."""
    global jwks_cache, jwks_cache_expiry
    
    # Check cache
    if jwks_cache and jwks_cache_expiry and datetime.now() < jwks_cache_expiry:
        return jwks_cache
        
    try:
        # If CLERK_ISSUER_URL isn't set, try to derive from secret or env
        # For now, we expect the user to provide the JWKS URL or ISSUER URL
        # Defaulting to a placeholder if not set, user must configure
        issuer = os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY")
        if not issuer:
             # Fallback logic or error
             pass
        
        # NOTE: In a real prod environment, you should set CLERK_JWKS_URL env var
        jwks_url = os.getenv("CLERK_JWKS_URL")
        
        if not jwks_url:
            # Try to build from frontend key if standard instance
            # This is tricky without the specific instance URL suitable for a template code
            # We will use a fallback or require the env var.
            raise ValueError("CLERK_JWKS_URL environment variable is missing")

        response = requests.get(jwks_url)
        response.raise_for_status()
        keys = response.json()
        
        jwks_cache = keys
        jwks_cache_expiry = datetime.now() + timedelta(hours=1)
        return keys
        
    except Exception as e:
        print(f"[AUTH] Failed to fetch JWKS: {e}")
        return {}

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Verify the JWT token and return the user payload.
    This acts as the 'Gatekeeper' dependency.
    """
    token = credentials.credentials
    
    try:
        # 1. Decode header to find Key ID (kid)
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        # 2. Get Public Key
        jwks = get_jwks()
        public_key = None
        
        if "keys" in jwks:
            for key in jwks["keys"]:
                if key.get("kid") == kid:
                    public_key = RSAAlgorithm.from_jwk(json.dumps(key))
                    break
        
        if not public_key:
            # If dynamic fetch failed, check if we have a static PEM (backup plan)
            if CLERK_PEM_PUBLIC_KEY:
                 public_key = CLERK_PEM_PUBLIC_KEY
            else:
                 raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: Key ID not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        # 3. Verify Token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            # Audience verification can be tricky if not configured, set verify=False if needed initially
            options={"verify_aud": False} 
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        print(f"[AUTH] Invalid token error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        print(f"[AUTH] Auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )
