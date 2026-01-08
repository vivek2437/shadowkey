# ShadowKey Deployment Guide

Complete guide for deploying ShadowKey to Vercel (frontend + backend).

## Prerequisites

- Vercel account ([signup here](https://vercel.com/signup))
- GitHub repository ([github.com/vivek2437/shadowkey](https://github.com/vivek2437/shadowkey))
- Vercel CLI (optional): `npm i -g vercel`

---

## Option 1: Deploy via Vercel Dashboard (Recommended)

### Step 1: Deploy Backend API

1. Go to [vercel.com/new](https://vercel.com/new)
2. Click **Import Project**
3. Import from GitHub: `vivek2437/shadowkey`
4. Configure:
   - **Framework Preset**: Other
   - **Root Directory**: `phase5/api`
   - **Build Command**: (leave empty)
   - **Output Directory**: (leave empty)
5. Click **Deploy**
6. Copy your backend URL (e.g., `https://shadowkey-api.vercel.app`)

### Step 2: Deploy Frontend

1. Click **Add New Project** again
2. Import the same repository: `vivek2437/shadowkey`
3. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `secure-flow-main/secure-flow-main`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Add Environment Variable:
   - **Name**: `VITE_API_BASE_URL`
   - **Value**: `https://shadowkey-api.vercel.app` (your backend URL)
5. Click **Deploy**

### Step 3: Test the Deployment

1. Visit your frontend URL (e.g., `https://shadowkey.vercel.app`)
2. Navigate to `/auth/sign-in`
3. Login and test keystroke + voice features
4. Check browser console for errors

---

## Option 2: Deploy via Vercel CLI

### Step 1: Install Vercel CLI

```bash
npm i -g vercel
vercel login
```

### Step 2: Deploy Backend

```bash
cd phase5/api
vercel --prod
```

When prompted:
- **Set up and deploy?** → Yes
- **Link to existing project?** → No
- **Project name?** → `shadowkey-api`
- **Root directory?** → `.` (current)

Copy the deployment URL.

### Step 3: Deploy Frontend

```bash
cd ../../secure-flow-main/secure-flow-main
```

Create `.env.production`:

```bash
VITE_API_BASE_URL=https://shadowkey-api.vercel.app
```

Deploy:

```bash
vercel --prod
```

When prompted:
- **Project name?** → `shadowkey`
- **Root directory?** → `.` (current)

---

## Configuration Details

### Frontend `vercel.json`

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

### Backend `vercel.json`

```json
{
  "version": 2,
  "builds": [
    {
      "src": "auth_service.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "auth_service.py"
    }
  ]
}
```

---

## Environment Variables

### Frontend

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `https://shadowkey-api.vercel.app` |

Set in Vercel Dashboard:
1. Go to **Project Settings** → **Environment Variables**
2. Add `VITE_API_BASE_URL`
3. Redeploy frontend

### Backend

No environment variables required for basic deployment.

---

## Troubleshooting

### Frontend shows "Failed to fetch"

**Cause**: Frontend can't reach backend API.

**Fix**:
1. Check `VITE_API_BASE_URL` is set correctly in Vercel
2. Ensure backend deployment is live
3. Check browser console for CORS errors

### Backend returns 404

**Cause**: Vercel routing misconfigured or wrong root directory.

**Fix**:
1. Ensure `vercel.json` exists in `phase5/api/`
2. Check root directory is set to `phase5/api` in Vercel dashboard
3. Redeploy backend

### Keystroke scores not updating

**Cause**: User not logged in via `/auth/sign-in` route.

**Fix**:
1. Navigate to `/auth/sign-in` (not direct to `/dashboard`)
2. Login with credentials
3. Session tokens will be stored in `sessionStorage`

### WebSocket connection fails

**Cause**: Vercel free tier has limited WebSocket support.

**Fix**:
- WebSockets may work with serverless functions on Vercel Pro
- For full WS support, consider deploying backend to Railway/Render
- Alternative: Use polling instead of WebSockets

---

## Custom Domain

1. Go to **Project Settings** → **Domains**
2. Add your custom domain (e.g., `shadowkey.yourdomain.com`)
3. Follow DNS configuration instructions
4. Update `VITE_API_BASE_URL` to use your backend's custom domain

---

## Production Checklist

- [ ] Backend deployed and accessible
- [ ] Frontend deployed with correct `VITE_API_BASE_URL`
- [ ] Test login flow end-to-end
- [ ] Verify keystroke capture works
- [ ] Test voice enrollment and verification
- [ ] Check all biometric scores update
- [ ] Confirm risk level transitions correctly
- [ ] Monitor Vercel logs for errors

---

## Redeployment

### Automatic Redeployment

Vercel auto-deploys on every push to `main` branch.

### Manual Redeployment

#### Frontend:
```bash
cd secure-flow-main/secure-flow-main
vercel --prod
```

#### Backend:
```bash
cd phase5/api
vercel --prod
```

---

## Monitoring

- **Vercel Dashboard**: View deployment logs and analytics
- **Browser Console**: Check for frontend errors
- **Network Tab**: Inspect API requests/responses

---

## Support

For deployment issues:
- Check [Vercel Docs](https://vercel.com/docs)
- Review [FastAPI on Vercel](https://vercel.com/docs/frameworks/python)
- Open an issue on [GitHub](https://github.com/vivek2437/shadowkey/issues)

---

**Note**: Free Vercel tier includes:
- Unlimited deployments
- 100GB bandwidth/month
- Serverless function limits (10s execution time)
- Limited WebSocket support

For production workloads, consider Vercel Pro or alternative hosting for the backend.
