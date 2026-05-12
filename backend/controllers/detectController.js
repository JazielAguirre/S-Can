const { analyzeImage } = require('../services/aiService');

const detectImage = async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No se recibió ninguna imagen.' });
  }

  try {
    const result = await analyzeImage(req.file);
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: 'Error al procesar la imagen.' });
  }
};

module.exports = { detectImage };
