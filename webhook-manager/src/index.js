const express = require('express')
const app = express()
const port = 3000

app.use(express.json())
app.get('/', (req, res) => {
  res.send('Hello World!')
})

// Questa è la "porta" dove busserà GitHub
app.post('/webhook', (req, res) => {
  const payload = req.body

  console.log('\n========================================')
  console.log('🔔 NUOVO WEBHOOK RICEVUTO DA GITHUB!')
  console.log('========================================')
  
  // Usiamo JSON.stringify con "null, 2" per stampare il JSON nel terminale 
  // bello formattato e impaginato, invece di una riga illeggibile.
  console.log(JSON.stringify(payload, null, 2))
  console.log('========================================\n')

  // Regola d'oro: rispondi SUBITO a GitHub con 200 OK
  res.status(200).send('Webhook ricevuto forte e chiaro!')
})

app.listen(port, () => {
  console.log(`webhook-receiver> Listening on port ${port}`)
})
