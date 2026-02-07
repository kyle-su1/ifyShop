import axios from 'axios';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const analyzeImage = async (file, token, options = {}) => {
    try {
        let base64Image = null;

        // Handle file input (Stages 1 & 2 if re-uploading) or skip if not provided
        if (file) {
            const toBase64 = (file) => new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.readAsDataURL(file);
                reader.onload = () => resolve(reader.result);
                reader.onerror = (error) => reject(error);
            });
            base64Image = await toBase64(file);
        }

        const response = await axios.post(`${API_URL}/analyze`, {
            image: base64Image || "", // Can be empty if skipping vision (though backend might need it for state, we'll see)
            user_query: "What is this item?",
            user_preferences: {},
            detect_only: options.detect_only || false,
            skip_vision: options.skip_vision || false,
            product_name: options.product_name || ""
        }, {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        });

        return response.data;
    } catch (error) {
        console.error("API Error:", error);
        throw error;
    }
};

/**
 * On-demand product identification using SerpAPI Google Lens.
 * Called when user clicks a bounding box to get specific product info.
 */
export const identifyObject = async (imageBase64, boundingBox, token) => {
    try {
        const response = await axios.post(`${API_URL}/api/v1/agent/identify`, {
            image_base64: imageBase64,
            bounding_box: boundingBox,
            object_index: 0
        }, {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        });
        return response.data;
    } catch (error) {
        console.error("Identify API Error:", error);
        throw error;
    }
};

