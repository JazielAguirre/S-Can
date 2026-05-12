const express = require('express');
const cors = require('cors');
const detectRouter = require('./routes/detect');

const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.json());

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'DogDex API funcionando' });
});

app.use('/api/detect', detectRouter);

// Captura errores de multer y los devuelve como JSON
app.use((err, req, res, next) => {
  if (err.code === 'LIMIT_FILE_SIZE') {
    return res.status(400).json({ error: 'El archivo supera el límite de 5 MB.' });
  }
  res.status(400).json({ error: err.message });
});

app.listen(PORT, () => {
  console.log(`Servidor DogDex corriendo en http://localhost:${PORT}`);
});
