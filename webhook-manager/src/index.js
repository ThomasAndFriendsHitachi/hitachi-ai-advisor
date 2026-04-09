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
    await redisConnection.lPush(queue_name, envelope);
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
