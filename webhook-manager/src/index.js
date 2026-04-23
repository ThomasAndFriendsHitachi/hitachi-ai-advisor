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
})

app.listen(port, () => {
  console.log(`Listening on port ${port}`)
})
