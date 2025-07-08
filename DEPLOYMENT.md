# Vercel Deployment Guide

## Prerequisites
- Vercel account
- GitHub repository connected to Vercel
- Python 3.8+ project

## Deployment Steps

### 1. Install Vercel CLI (Optional)
```bash
npm i -g vercel
```

### 2. Deploy via Vercel Dashboard
1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your GitHub repository
4. Configure build settings:
   - **Framework Preset**: Other
   - **Build Command**: Leave empty
   - **Output Directory**: Leave empty
   - **Install Command**: `pip install -r requirements.txt`

### 3. Environment Variables (Optional)
Add these in Vercel dashboard under Settings > Environment Variables:
- `FLASK_ENV`: `production`
- `SECRET_KEY`: Your secret key

### 4. Deploy
Click "Deploy" and wait for the build to complete.

## Important Notes

### Serverless Limitations
- **File Storage**: Uses `/tmp` directory (temporary)
- **File Size**: Limited to 16MB per upload
- **Execution Time**: Limited to 10 seconds (Hobby plan)
- **Memory**: Limited to 1024MB

### Recommendations
1. **For Production**: Consider using cloud storage (AWS S3, Google Cloud Storage)
2. **Large Files**: Implement chunked uploads
3. **Long Processing**: Use background jobs or external services
4. **Database**: Use cloud databases instead of local files

### Troubleshooting
- Check Vercel function logs for errors
- Ensure all dependencies are in `requirements.txt`
- Verify file paths use `/tmp` for temporary storage
- Test locally with `vercel dev`

## Local Testing
```bash
# Install Vercel CLI
npm i -g vercel

# Test locally
vercel dev

# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

## Project Structure
```
/
├── api/
│   └── index.py          # Vercel entrypoint
├── flashlog/             # Your Flask app
├── logai/               # LogAI library
├── requirements.txt     # Python dependencies
├── vercel.json         # Vercel configuration
└── .vercelignore       # Files to exclude
``` 