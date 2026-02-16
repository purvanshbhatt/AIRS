# ResilAI Authentication Integration Guide

This document describes how to integrate Firebase Authentication into ResilAI.

## Current State

Authentication is **scaffolded but not active**:
- **Local mode**: All requests are allowed without authentication
- **Production mode**: Bearer token is required (returns 401 if missing)

## Architecture

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   React App     â”‚â”€â”€â”€â”€â–¶â”‚   FastAPI       â”‚â”€â”€â”€â”€â–¶â”‚  Firebase Admin â”‚
â”‚   AuthContext   â”‚     â”‚   get_current_  â”‚     â”‚  (verify token) â”‚
â”‚   getToken()    â”‚     â”‚   user()        â”‚     â”‚                 â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
        â”‚                       â”‚
        â”‚                       â”‚
        â–¼                       â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Firebase Auth  â”‚     â”‚  User object    â”‚
â”‚  (client SDK)   â”‚     â”‚  uid, email,    â”‚
â”‚  signIn, etc.   â”‚     â”‚  name           â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## Frontend Integration Steps

### 1. Install Firebase SDK

```bash
cd frontend
npm install firebase
```

### 2. Create Firebase Config

Create `frontend/src/lib/firebase.ts`:

```typescript
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
};

export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
```

### 3. Add Environment Variables

Create/update `frontend/.env`:

```env
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
```

### 4. Update AuthContext

Update `frontend/src/contexts/AuthContext.tsx`:

```typescript
import { auth } from '../lib/firebase';
import { 
  onAuthStateChanged, 
  signInWithPopup, 
  GoogleAuthProvider,
  signOut as firebaseSignOut 
} from 'firebase/auth';

// In AuthProvider:

useEffect(() => {
  const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
    if (firebaseUser) {
      setUser({
        uid: firebaseUser.uid,
        email: firebaseUser.email,
        displayName: firebaseUser.displayName,
        photoURL: firebaseUser.photoURL,
      });
    } else {
      setUser(null);
    }
    setLoading(false);
  });
  return unsubscribe;
}, []);

const getToken = useCallback(async () => {
  return auth.currentUser?.getIdToken() ?? null;
}, []);

const signIn = useCallback(async () => {
  const provider = new GoogleAuthProvider();
  await signInWithPopup(auth, provider);
}, []);

const signOut = useCallback(async () => {
  await firebaseSignOut(auth);
  setUser(null);
}, []);
```

## Backend Integration Steps

### 1. Install Firebase Admin SDK

```bash
pip install firebase-admin
```

### 2. Add to Requirements

Update `requirements.txt`:

```
firebase-admin>=6.0.0
```

### 3. Initialize Firebase Admin

Update `app/main.py`:

```python
import firebase_admin
from firebase_admin import credentials

# Initialize on startup
@app.on_event("startup")
def init_firebase():
    if settings.is_prod:
        # Uses Application Default Credentials on Cloud Run
        firebase_admin.initialize_app()
```

### 4. Update Auth Module

Update `app/core/auth.py`:

```python
from firebase_admin import auth as firebase_auth

def verify_firebase_token(token: str) -> dict:
    try:
        decoded = firebase_auth.verify_id_token(token)
        return {
            "uid": decoded["uid"],
            "email": decoded.get("email"),
            "name": decoded.get("name"),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )
```

### 5. Protect Routes

Apply auth to routes in `app/api/*.py`:

```python
from app.core.auth import require_auth, get_current_user, User

# Option A: Require auth without accessing user
@router.post("/", dependencies=[Depends(require_auth)])
def create_item(...):
    ...

# Option B: Access authenticated user
@router.get("/profile")
def get_profile(user: User = Depends(require_auth)):
    return {"uid": user.uid, "email": user.email}

# Option C: Optional auth (works in local mode)
@router.get("/public-or-private")
def flexible_route(user: Optional[User] = Depends(get_current_user)):
    if user:
        return {"message": f"Hello {user.email}"}
    return {"message": "Hello anonymous"}
```

## Cloud Run Configuration

### Service Account Permissions

The Cloud Run service account needs the `Firebase Authentication Admin` role:

```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/firebaseauth.admin"
```

### Environment Variables

Set these in Cloud Run:

```bash
gcloud run services update airs \
  --set-env-vars="ENV=prod"
```

## Testing

### Local Development

In local mode (`ENV=local`), authentication is bypassed:
- Frontend: `getToken()` returns `null`
- Backend: `get_current_user()` returns `None`
- Backend: `require_auth()` returns a mock dev user

### Production Testing

Test with a real Firebase token:

```bash
# Get token from Firebase client
TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."

# Test API
curl -H "Authorization: Bearer $TOKEN" \
  https://your-api.run.app/api/orgs
```

### Test 401 Response

```bash
# Without token in prod mode
curl https://your-api.run.app/api/orgs
# Returns: {"detail": "Authentication required"}
```

## File Reference

| File | Purpose |
|------|---------|
| `frontend/src/contexts/AuthContext.tsx` | React auth state and methods |
| `frontend/src/api.ts` | API client with token injection |
| `app/core/auth.py` | FastAPI auth dependencies |
| `app/core/config.py` | Environment detection |

## Security Considerations

1. **Never commit Firebase credentials** - Use environment variables
2. **Validate tokens server-side** - Don't trust client-only auth
3. **Use HTTPS in production** - Required for secure cookies
4. **Restrict CORS in production** - Set specific origins
5. **Audit auth bypass in local mode** - Ensure `ENV=prod` is set in production
