import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import compression from 'compression';

// Helper for __dirname in modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// Enable gzip compression
app.use(compression());

// Serve static files from the dist directory
app.use(express.static(path.join(__dirname, 'dist')));

// API Proxy (optional - handy if you want to keep same API structure)
// But essentially we just want to serve the frontend app
// If the frontend makes calls to /api, we can proxy them to the python backend
// or the frontend can call the python backend directly (CORS required).
// For now, let's keep it simple and just serve the app.

// Handle React routing, return all requests to React app
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
