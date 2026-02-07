const express = require('express');
const cors = require('cors');
require('dotenv').config();

const app = express();
const port = 3001;

app.use(cors());
app.use(express.json({ limit: '50mb' }));

app.post('/api/analyze', async (req, res) => {
    try {
        const { imageBase64 } = req.body;
        console.log(`\n--- New Request Received ---`);
        console.log(`Raw Body imageBase64 type: ${typeof imageBase64}`);
        console.log(`Raw Body imageBase64 length: ${imageBase64 ? imageBase64.length : 'UNDEFINED'}`);
        if (imageBase64) console.log(`Raw Body imageBase64 preview: ${imageBase64.substring(0, 100)}...`);

        const apiKey = process.env.GOOGLE_API_KEY;

        if (!apiKey) {
            return res.status(500).json({
                error: 'API Key not found',
                details: 'Please add GOOGLE_API_KEY to your backend/.env file'
            });
        }

        if (!imageBase64) {
            return res.status(400).json({ error: 'No image data provided' });
        }

        // Robustly remove header: split by 'base64,' if present
        let base64Data = imageBase64;
        if (imageBase64.includes('base64,')) {
            base64Data = imageBase64.split('base64,')[1];
        }

        console.log(`Received Image Data. Total Length: ${imageBase64.length}`);
        console.log(`Extracted Base64 Length: ${base64Data.length}`);
        console.log(`Base64 Preview (first 50 chars): ${base64Data.substring(0, 50)}...`);

        // Prepare request body for Google Cloud Vision REST API
        const requestBody = {
            requests: [
                {
                    image: {
                        content: base64Data
                    },
                    features: [
                        { type: 'OBJECT_LOCALIZATION' },
                        { type: 'LABEL_DETECTION' },
                        { type: 'TEXT_DETECTION' } // Add TEXT_DETECTION just in case to test
                    ]
                }
            ]
        };

        // Make direct fetch call
        console.log(`Sending request to Vision API with Key: ${apiKey ? 'Present' : 'MISSING'}`);

        const response = await fetch(
            `https://vision.googleapis.com/v1/images:annotate?key=${apiKey}`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            }
        );

        const data = await response.json();
        console.log('Vision API Response Status:', response.status);
        console.log('Vision API Full Response:', JSON.stringify(data, null, 2)); // Full log

        if (!response.ok) {
            console.error('Vision API Error Body:', JSON.stringify(data, null, 2));
            throw new Error(data.error?.message || 'API request failed');
        }

        const result = data.responses[0];

        res.json({
            objects: result.localizedObjectAnnotations || [],
            labels: result.labelAnnotations || [],
        });

    } catch (error) {
        console.error('Vision API Error:', error);
        res.status(500).json({ error: 'Failed to analyze image', details: error.message });
    }
});

app.listen(port, () => {
    console.log(`Backend server running at http://localhost:${port}`);
    const key = process.env.GOOGLE_API_KEY;
    console.log(`API Key Status: ${key ? 'Loaded (' + key.substring(0, 5) + '...)' : 'MISSING'}`);
});
