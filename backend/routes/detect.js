const express = require('express');
const router = express.Router();
const upload = require('../middlewares/upload');
const { detectImage } = require('../controllers/detectController');

// POST /api/detect — recibe una imagen con el campo "image"
router.post('/', upload.single('image'), detectImage);

module.exports = router;
