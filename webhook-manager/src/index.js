const express = require('express');
const redis = require('redis');
const { v4: uuidv4 } = require('uuid'); //Used to generate UUIDs

//Express configuration
const app = express();
//In case env var are configured
const port = process.env.PORT || 3000;

//Redis configuration
const redisUrl = process.env.REDIS_URL || 'redis://redis_broker:6379';
const redisConnection = redis.createClient({ url: redisUrl });
const queue_name = process.env.REDIS_QUEUE_NAME || 'queue:ai_tasks'
redisConnection.on('error', (err) => console.error('Error connecting to Redis:', err));

(async () =>{
  await redisConnection.connect();
  console.log('Successfully connected to Redis.');
})();

app.use(express.json());

//url to use in github action
app.post('/webhook', async(req, res) => {
  const payload = req.body;
  const eventType = req.headers['x-github-event'];

  // Logic to determine the project name from the GitHub payload
  const projectName = payload.project_name || (payload.repository ? payload.repository.full_name : "Manual Trigger");

  try {
    const envelope = JSON.stringify({
      id: uuidv4(),
      timestamp: new Date().toISOString(),
      type: eventType,
      source: "github_webhook",
      payload: {
          ...payload,
          project_name: projectName // Ensure the worker finds this key easily
      }
    });
    console.log(envelope)
    // Push the structured envelope to Redis
    await redisConnection.lPush(queue_name, envelope);
    console.log(`Queued: ${projectName}`);

    res.status(202).json({ message: "Accepted", project: projectName });
  } catch(err) {
    console.error('Redis Push Error:', err);
    res.status(500).send('Internal Server Error');
  }
});

app.listen(port, () => {
  console.log(`Listening on port ${port}`)
})