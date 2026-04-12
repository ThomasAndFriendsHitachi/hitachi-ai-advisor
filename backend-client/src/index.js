const express = require('express');
const cors = require('cors');
const redis = require('redis');
const { Pool } = require('pg');

const app = express();
// Using 3001 so it doesn't clash with WebServer #1 on 3000
const port = process.env.PORT || 3001; 

app.use(cors());
app.use(express.json());

// --- 1. Database Connection ---
const pool = new Pool({
    connectionString: process.env.DATABASE_URL
});

pool.on('error', (err) => {
    console.error('Unexpected error on idle client', err);
});

// --- 2. Redis Subscriber ---
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
        // Note: For now we just log it. Later, we can use Socket.io here 
        // to push this directly to the React frontend
    });
})();

// --- 3. REST API Endpoints ---

// Get all AI tasks (Cases)
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
        // Fetch user from DB
        const result = await pool.query('SELECT * FROM users WHERE username = $1', [username]);
        
        if (result.rows.length > 0) {
            const user = result.rows[0];
            // Note: In production we would use bcrypt.compare() here.
            // For now, if the user exists, we let them in.
            res.json({
                success: true,
                token: "mock-jwt-token-123",
                user: {
                    id: user.id,
                    username: user.username,
                    email: user.mail,
                    name: user.username
                }
            });
        } else {
            res.status(401).json({ success: false, error: 'Invalid credentials' });
        }
    } catch(err) {
        console.error('Auth Error:', err);
        res.status(500).json({ error: 'Server error' });
    }
});

app.listen(port, () => {
    console.log(`Backend API Server running on port ${port}`);
});