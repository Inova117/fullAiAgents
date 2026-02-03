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
        jwks_url = os.getenv("CLERK_JWKS_URL")
        
        # Fallback: Try to construct from ISSUER_URL
        if not jwks_url:
            issuer = os.getenv("CLERK_ISSUER_URL")
            if issuer:
                # Remove trailing slash if present
                issuer = issuer.rstrip("/")
                jwks_url = f"{issuer}/.well-known/jwks.json"
                print(f"[AUTH] Derived JWKS URL from Issuer: {jwks_url}")
        
        if not jwks_url:
            print("[AUTH] ERROR: CLERK_JWKS_URL and CLERK_ISSUER_URL are both missing.")
            return {}

        print(f"[AUTH] Fetching JWKS from: {jwks_url}")
        response = requests.get(jwks_url, timeout=10)
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
                 print(f"[AUTH] Token KID {kid} not found in JWKS. Available KIDs: {[k.get('kid') for k in jwks.get('keys', [])]}")
                 raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token: Key ID {kid} not found",
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
