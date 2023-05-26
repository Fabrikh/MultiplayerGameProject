const express = require('express');
const app = express();

app.use(express.json());

app.post('/api/send', (req, res) => {
  // Handle sending JSON messages
  const message = req.body;
  // Process the message and send it to the other Docker container

  res.json({ success: true });
});

app.get('/api/receive', (req, res) => {
  // Handle receiving JSON messages
  // Receive messages from the other Docker container

  const message = { hello: 'world' }; // Replace with the received message
  res.json(message);
});

const port = 3000;
app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
