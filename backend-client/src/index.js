const express = require('express');
const cors = require('cors');
const redis = require('redis');
const { Pool } = require('pg');
const http = require('http');
const { Server } = require('socket.io');

const app = express();
const port = process.env.PORT || 3001;

// Wrap Express with HTTP Server for Socket.io
const server = http.createServer(app);
const io = new Server(server, {
    cors: {
        origin: '*', // In production, restrict this to your frontend domain
        methods: ['GET', 'POST', 'PUT'] // Make sure PUT is allowed for the new route
    }
});

app.use(cors());
app.use(express.json());

// --- 1. Database Connection ---
const pool = new Pool({
    connectionString: process.env.DATABASE_URL
});

pool.on('error', (err) => {
    console.error('Unexpected error on idle client', err);
});

// --- 2. WebSocket Connection Handling ---
io.on('connection', (socket) => {
    console.log(`[Socket.io] Client connected: ${socket.id}`);
    socket.on('disconnect', () => {
        console.log(`[Socket.io] Client disconnected: ${socket.id}`);
    });
});

// --- 3. Redis Subscriber ---
const redisUrl = process.env.REDIS_URL || 'redis://redis_broker:6379';
const redisSubscriber = redis.createClient({ url: redisUrl });

redisSubscriber.on('error', (err) => console.error('Redis Error:', err));

(async () => {
    await redisSubscriber.connect();
    console.log('Successfully connected to Redis Subscriber.');

    const channelName = process.env.REDIS_CHANNEL_NAME || 'channel:task_updates';
    
    // Listen for the AI Agent publishing updates
    await redisSubscriber.subscribe(channelName, (message) => {
        console.log(`\n[REDIS Pub/Sub] Alert on ${channelName}:`, message);
        
        // Broadcast the update to all connected React clients!
        io.emit('task_updated', JSON.parse(message));
    });
})();

// --- 4. REST API Endpoints ---
app.get('/api/cases', async (req, res) => {
    try {
        const result = await pool.query('SELECT * FROM ai_tasks_results ORDER BY processed_at DESC');
        res.json(result.rows);
    } catch (err) {
        console.error('DB Error:', err);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

// Get a specific case by ID
app.get('/api/cases/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const result = await pool.query('SELECT * FROM ai_tasks_results WHERE id = $1', [id]);
        if (result.rows.length === 0) return res.status(404).json({ error: 'Not found' });
        res.json(result.rows[0]);
    } catch (err) {
        console.error('DB Error:', err);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

// Update Case Status and Trigger GitHub Pipeline
app.put('/api/cases/:id/status', async (req, res) => {
    const { id } = req.params;
    const { status } = req.body; // Expects 'Approved' or 'Rejected'

    try {
        // 1. Update DB and get the raw_payload back
        const updateQuery = `
            UPDATE ai_tasks_results 
            SET status = $1 
            WHERE id = $2 
            RETURNING raw_payload;
        `;
        const result = await pool.query(updateQuery, [status, id]);

        if (result.rows.length === 0) {
            return res.status(404).json({ error: 'Case not found' });
        }

        const payload = result.rows[0].raw_payload;

        // 2. Extract repository and commit SHA from the GitHub payload safely
        // Different GitHub events (push, pull_request) store these in slightly different places
        const owner = payload.repository?.owner?.login || payload.repository?.owner?.name;
        const repo = payload.repository?.name;
        const sha = payload.pull_request?.head?.sha || payload.after || payload.head_commit?.id;

        if (owner && repo && sha) {
            // 3. Map our UI status to GitHub's required pipeline states
            const githubState = status === 'Approved' ? 'success' : 'failure';
            const description = status === 'Approved' ? 'Release approved by Hitachi Manager' : 'Release rejected by Hitachi Manager';

            // 4. Send the command to Webserver 1 (Webhook Manager)
            // In Docker, 'webhook-manager' is the host name of the container
            const ws1Url = process.env.WS1_URL || 'http://webhook-manager:3000';
            
            // Fire and forget (don't await) so the React UI responds instantly
            fetch(`${ws1Url}/update-github-status`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ owner, repo, sha, state: githubState, description })
            })
            .then(ws1Response => {
                if (!ws1Response.ok) {
                    console.error(`Warning: WS1 returned status ${ws1Response.status}`);
                } else {
                    console.log(`[WS2 -> WS1] Forwarded GitHub status update for ${sha}`);
                }
            })
            .catch(err => console.error("Failed to reach WS1:", err));
            
        } else {
            console.warn("Could not extract owner, repo, or sha from payload. Skipping GitHub update.");
        }

        res.json({ message: 'Status updated successfully', status });

    } catch (err) {
        console.error('Error updating status:', err);
        res.status(500).json({ error: 'Failed to update status' });
    }
});

// Basic Login Endpoint
app.post('/api/auth/login', async (req, res) => {
    const { username, password } = req.body;
    try {
        const result = await pool.query('SELECT * FROM users WHERE username = $1', [username]);
        if (result.rows.length > 0) {
            const user = result.rows[0];
            res.json({
                success: true,
                token: "mock-jwt-token-123",
                user: { id: user.id, username: user.username, email: user.mail, name: user.username }
            });
        } else {
            res.status(401).json({ success: false, error: 'Invalid credentials' });
        }
    } catch(err) {
        console.error('Auth Error:', err);
        res.status(500).json({ error: 'Server error' });
    }
});

// IMPORTANT: Use server.listen instead of app.listen
server.listen(port, () => {
    console.log(`Backend API & WebSocket Server running on port ${port}`);
});