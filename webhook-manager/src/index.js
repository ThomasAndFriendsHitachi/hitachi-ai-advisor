const express = require('express');
const redis = require('redis');
const { v4: uuidv4 } = require('uuid');
const path = require('path');
const { S3Client, PutObjectCommand, CreateBucketCommand, HeadBucketCommand } = require("@aws-sdk/client-s3");

// Express configuration
const app = express();
const port = process.env.PORT || 3000;

// Token secrets
const WEBHOOK_SECRET = process.env.GITHUB_WEBHOOK_SECRET || 'my-secret';
const GITHUB_TOKEN = process.env.WEBHOOK_REPO_TOKEN; 

// --- S3 / MinIO Configuration ---
const BUCKET_NAME = process.env.MINIO_BUCKET_NAME || 'hitachi-ingestion';
const s3Client = new S3Client({
  region: "us-east-1", // MinIO default
  endpoint: process.env.MINIO_ENDPOINT || "http://minio:9000",
  forcePathStyle: true, // Mandatory for MinIO to work properly instead of AWS
  credentials: {
    accessKeyId: process.env.MINIO_ACCESS_KEY || "admin",
    secretAccessKey: process.env.MINIO_SECRET_KEY || "SuperSecretMinio123!"
  }
});

// --- Redis configuration ---
const redisUrl = process.env.REDIS_URL || 'redis://redis_broker:6379';
const redisConnection = redis.createClient({ url: redisUrl });

redisConnection.on('error', (err) => console.error('Error connecting to Redis:', err));

// Ensure the MinIO bucket exists on startup
async function initBucket() {
  try {
    await s3Client.send(new HeadBucketCommand({ Bucket: BUCKET_NAME }));
    console.log(`MinIO Bucket '${BUCKET_NAME}' found.`);
  } catch (err) {
    if (err.name === 'NotFound' || err.$metadata?.httpStatusCode === 404) {
      console.log(`Creating MinIO Bucket '${BUCKET_NAME}'...`);
      await s3Client.send(new CreateBucketCommand({ Bucket: BUCKET_NAME }));
      console.log('Bucket created successfully!');
    } else {
      console.error("Error checking MinIO bucket (might be starting up):", err.message);
    }
  }
}

(async () => {
  await redisConnection.connect();
  console.log('Successfully connected to Redis.');
  await initBucket();
})();

app.use(express.json());

// --- Extensions and Filters ---
const SUPPORTED_EXTENSIONS = new Set([
  '.txt', '.md', '.rst', '.log', '.ini', '.cfg', '.conf', '.yaml', '.yml',
  '.xml', '.html', '.htm', '.sql', '.sh', '.bash', '.zsh', '.bat', '.cmd', '.ps1',
  '.py', '.js', '.ts', '.java', '.c', '.cpp', '.cs', '.go', '.rb', '.php',
  '.docx', '.doc', '.pdf', '.csv', '.xls', '.xlsx', '.json'
]);

function isSupportedFile(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  if (!ext) return true; // Files without an extension (e.g., Dockerfile, Makefile) are accepted
  return SUPPORTED_EXTENSIONS.has(ext);
}

// --- Helper: Download from GitHub and upload to MinIO ---
async function processAndUploadFile(repoFullName, commitSha, originalFilePath, objectKey) {
  const url = `https://raw.githubusercontent.com/${repoFullName}/${commitSha}/${originalFilePath}`;
  
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github.v3.raw'
    }
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch ${originalFilePath}: ${response.statusText}`);
  }

  // Read as a binary array to support large files and Office/PDF documents without corruption
  const arrayBuffer = await response.arrayBuffer();
  const buffer = Buffer.from(arrayBuffer);
  
  // Upload to MinIO
  await s3Client.send(new PutObjectCommand({
    Bucket: BUCKET_NAME,
    Key: objectKey,
    Body: buffer
  }));
}

// --- WEBHOOK ENDPOINT (Custom Action via cURL) ---
app.post('/webhook', async (req, res) => {
  
  // Validation via Bearer Token sent by your GitHub Action
  const authHeader = req.headers['authorization'];
  if (!authHeader || authHeader !== `Bearer ${WEBHOOK_SECRET}`) {
    console.warn("Received webhook with invalid or missing Bearer token");
    return res.status(401).send("Invalid signature");
  }

  const payload = req.body;
  const jobId = payload.commit_sha;

  console.log('\n========================================');
  console.log(`NEW PIPELINE JOB: ${jobId}`);
  console.log('========================================');

  try {
    // 1. Extract the list of added or modified files sent by the Action
    const rawFiles = [
      ...(payload.files?.added || []),
      ...(payload.files?.modified || [])
    ];

    // 2. Filter based on supported extensions
    const validFiles = rawFiles.filter(isSupportedFile);
    const numFiles = validFiles.length;

    console.log(`Total files in commit: ${rawFiles.length} | Supported files to process: ${numFiles}`);

    if (numFiles === 0) {
      console.log("No supported files to process.");
      return res.status(200).send("No processable files.");
    }

    // 3. Set state counters in Redis to let the AI Agent know when the job is finished
    await redisConnection.set(`job:${jobId}:pending`, numFiles);
    await redisConnection.set(`job:${jobId}:metadata`, JSON.stringify({
      project: payload.project_name,
      author: payload.author,
      message: payload.commit_message,
      dev_phase: payload.development_phase,
      security_scan: payload.security_scan_results
    }));

    // 4. For each valid file: Fetch -> Upload to MinIO -> Queue in Redis
    for (const originalPath of validFiles) {
      console.log(`[Job ${jobId}] Transferring to MinIO: ${originalPath}...`);
      
      const objectKey = `commits/${jobId}/${originalPath}`;
      
      // Upload to S3/MinIO
      await processAndUploadFile(payload.project_name, jobId, originalPath, objectKey);

      // Create the "Lightweight" task ticket for the AI Agent
      const ticket = {
        task_id: uuidv4(),
        job_id: jobId,
        type: "parse_file",
        original_github_path: originalPath,
        s3_uri: `s3://${BUCKET_NAME}/${objectKey}` 
      };

      await redisConnection.lPush('queue:ai_tasks', JSON.stringify(ticket));
    }

    console.log(`[Job ${jobId}] Queuing completed successfully.`);
    res.status(202).send("Accepted and queued successfully");

  } catch (err) {
    console.error('Error processing webhook:', err);
    res.status(500).send('Internal Server Error');
  }
});

// --- GITHUB STATUS ENDPOINT (Intact) ---
app.post('/update-github-status', async (req, res) => {
  const { owner, repo, sha, state, description } = req.body;
  const token = process.env.WEBHOOK_REPO_TOKEN;

  if (!token) {
    console.error("Missing WEBHOOK_REPO_TOKEN in environment variables.");
    return res.status(500).json({ error: "GitHub token not configured" });
  }

  if (!owner || !repo || !sha || !state) {
    return res.status(400).json({ error: "Missing required fields (owner, repo, sha, state)" });
  }

  try {
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
        state: state,
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
  console.log(`Webhook Manager listening on port ${port}`);
});