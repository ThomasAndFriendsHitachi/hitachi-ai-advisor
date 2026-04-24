const express = require('express');
const redis = require('redis');
const { v4: uuidv4 } = require('uuid'); //Used to generate UUIDs
const crypto = require('crypto');

//Express configuration
const app = express();
//In case env var are configured
const port = process.env.PORT || 3000;

const WEBHOOK_SECRET = process.env.GITHUB_WEBHOOK_SECRET || 'my-secret';

//Redis configuration
const redisUrl = process.env.REDIS_URL || 'redis://redis_broker:6379';
const redisConnection = redis.createClient({ url: redisUrl });

redisConnection.on('error', (err) => console.error('Error connecting to Redis:', err));

(async () =>{
  await redisConnection.connect();
  console.log('Successfully connected to Redis.');
})();

app.use(express.json({
  verify: (req, res, buf) => {
    req.rawBody = buf;
  }
}));

// Helper function to verify github signature
function verifyGitHubSignature(req) {
  const signature = req.headers['x-hub-signature-256'];
  if (!signature) return false;

  const hmac = crypto.createHmac('sha256', WEBHOOK_SECRET);
  const digest = 'sha256=' + hmac.update(req.rawBody).digest('hex');

  try {
    return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(digest));
  } catch (e) {
    return false;
  }
}

//url to use in github action
app.post('/webhook', async(req, res) => {

  if (!verifyGitHubSignature(req)){
    console.warn("Received webhook with invalid of missing signature");
    return res.status(401).send("Invalid signature");
  }

  const payload = req.body;
  const eventType = req.headers['x-github-event'];

  console.log('\n========================================')
  console.log(`NEW WEBHOOK: ${eventType}`)
  console.log('========================================')
  
  //Prints the contents of webhook json
  console.log(JSON.stringify(payload, null, 2))
  console.log('========================================\n')


  try{
    const envelope = JSON.stringify({
      id: uuidv4(),
      timestamp: new Date().toISOString(),
      type: eventType,
      source: "github_webhook",
      payload: payload
    });
    //Add this message to te list ai_tasks
    await redisConnection.lPush('queue:ai_tasks', envelope);
    console.log("Added to redis queue");

    res.status(202).send("Accepted and queued");
  }catch(err){
    console.error('Error sending to Redis...', err);
    res.status(500).send('Internal Server Error');
  }
});


// Receive decisions from WS2 and update GitHub Commit Status
app.post('/update-github-status', async (req, res) => {
  const { owner, repo, sha, state, description } = req.body;
  
  // Using the specific variable name you requested
  const token = process.env.WEBHOOK_REPO_TOKEN;

  if (!token) {
    console.error("Missing WEBHOOK_REPO_TOKEN in environment variables.");
    return res.status(500).json({ error: "GitHub token not configured" });
  }

  if (!owner || !repo || !sha || !state) {
    return res.status(400).json({ error: "Missing required fields (owner, repo, sha, state)" });
  }

  try {
    // GitHub Commit Status REST API URL
    const githubUrl = `https://api.github.com/repos/${owner}/${repo}/statuses/${sha}`;
    
    const response = await fetch(githubUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
        'X-GitHub-Api-Version': '2022-11-28'
      },
      body: JSON.stringify({
        state: state, // GitHub expects: 'success', 'failure', 'pending', or 'error'
        description: description,
        context: 'Hitachi AI Advisor'
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`GitHub API returned ${response.status}: ${errorText}`);
    }

    console.log(`Successfully updated GitHub status for ${sha} to [${state}]`);
    res.status(200).json({ message: "GitHub status updated successfully" });

  } catch (err) {
    console.error('Error updating GitHub status:', err.message);
    res.status(500).json({ error: 'Failed to update GitHub' });
  }
});

app.listen(port, () => {
  console.log(`Listening on port ${port}`)
});