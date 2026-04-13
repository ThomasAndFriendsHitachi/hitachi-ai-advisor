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
        methods: ['GET', 'POST']
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