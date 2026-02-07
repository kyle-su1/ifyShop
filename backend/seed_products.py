import logging
import time
from typing import List, Dict
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.services.snowflake_vector import snowflake_vector_service
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample Product Data
SAMPLE_PRODUCTS = [
    {
        "id": "prod_Sony_WH1000XM5",
        "name": "Sony WH-1000XM5 Wireless Noise Canceling Headphones",
        "description": "Industry-leading noise cancellation, exceptional sound quality, and crystal-clear hands-free calling. up to 30-hour battery life with quick charging.",
        "price": 348.00,
        "image_url": "https://m.media-amazon.com/images/I/51SKmu2G9FL._AC_SL1000_.jpg",
        "source_url": "https://electronics.sony.com/audio/headphones/headband/p/wh1000xm5-b"
    },
    {
        "id": "prod_Bose_QC45",
        "name": "Bose QuietComfort 45 Bluetooth Wireless Noise Cancelling Headphones",
        "description": "Iconic quiet, comfort, and sound. World-class noise cancelling technology with a noise-rejecting microphone system for clear calls.",
        "price": 279.00,
        "image_url": "https://assets.bose.com/content/dam/Bose_DAM/Web/consumer_electronics/global/products/headphones/qc45/product_silo_images/QC45_Black_Ecom_01.png/_jcr_content/renditions/cq5dam.web.1280.1280.png",
        "source_url": "https://www.bose.com/en_us/products/headphones/noise_cancelling_headphones/quietcomfort-headphones-45.html"
    },
    {
        "id": "prod_Apple_AirPodsMax",
        "name": "Apple AirPods Max Wireless Over-Ear Headphones",
        "description": "High-fidelity audio. Active Noise Cancellation with Transparency mode. Spatial audio for theater-like sound that surrounds you.",
        "price": 549.00,
        "image_url": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/airpods-max-select-silver-202011?wid=940&hei=1112&fmt=png-alpha&.v=1604021221000",
        "source_url": "https://www.apple.com/airpods-max/"
    },
    {
        "id": "prod_Dyson_V15",
        "name": "Dyson V15 Detect Cordless Vacuum",
        "description": "Powerful cordless vacuum with laser illumination. Scientific proof of a deep clean. Piezo sensor counts and measures the size of dust particles.",
        "price": 749.99,
        "image_url": "https://dyson-h.assetsadobe2.com/is/image/content/dam/dyson/images/products/vacuum-cleaners/v15-detect/v15-detect-yellow-gold/V15-Detect-Yellow-Gold-Hero.jpg",
        "source_url": "https://www.dyson.com/vacuum-cleaners/cordless/v15-detect"
    },
    {
        "id": "prod_Logitech_MXMaster3S",
        "name": "Logitech MX Master 3S Performance Wireless Mouse",
        "description": "An icon remastered. Feel every moment of your workflow with even more precision, tactility, and performance, thanks to Quiet Clicks and an 8,000 DPI track-on-glass sensor.",
        "price": 99.99,
        "image_url": "https://resource.logitech.com/w_692,c_lpad,ar_4:3,q_auto,f_auto,dpr_1.0/d_transparent.gif/content/dam/logitech/en/products/mice/mx-master-3s/gallery/mx-master-3s-graphite-top.png?v=1",
        "source_url": "https://www.logitech.com/en-us/products/mice/mx-master-3s.html"
    },
     {
        "id": "prod_HermanMiller_Aeron",
        "name": "Herman Miller Aeron Chair",
        "description": "Ergonomic office chair with Pellicle suspension and PostureFit SL support. Adjustable arms, tilt limiter, and seat angle.",
        "price": 1650.00,
        "image_url": "https://s7d2.scene7.com/is/image/hermanmiller/200720_Aeron_Refined_BK_1?wid=800&hei=800&qlt=85,0&resMode=sharp2",
        "source_url": "https://store.hermanmiller.com/office-chairs-aeron/aeron-chair/2195348.html"
    },
    {
        "id": "prod_Steelcase_Leap",
        "name": "Steelcase Leap V2 Office Chair",
        "description": "High performance ergonomic chair. LiveBack technology that changes shape to mimic and support the movement of your spine.",
        "price": 1299.00,
        "image_url": "https://store.steelcase.com/dw/image/v2/BBCC_PRD/on/demandware.static/-/Sites-steelcase-master-catalog/default/dw1554900c/images/products/Leap/Leap_Black_46216179.jpg?sw=800&sh=800&sm=fit",
        "source_url": "https://store.steelcase.com/seating/office-chairs/leap"
    }
]

def seed_products():
    print(f"Starting Snowflake seeding with {len(SAMPLE_PRODUCTS)} products...")
    
    # 1. Initialize Embeddings
    try:
        embeddings_model = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=settings.GOOGLE_API_KEY
        )
    except Exception as e:
        logger.error(f"Failed to initialize Gemni Embeddings: {e}")
        return

    success_count = 0
    
    # 2. Loop and Insert
    for product in SAMPLE_PRODUCTS:
        product_name = product['name']
        print(f"Processing: {product_name}...")
        
        try:
            # Generate Embedding
            # We combine name and description for better semantic search
            text_to_embed = f"{product['name']} - {product['description']}"
            vector = embeddings_model.embed_query(text_to_embed)
            
            if not vector:
                print(f"  -> Failed to generate vector for {product_name}")
                continue
            
            print(f"  -> Generated vector with dimension: {len(vector)}")

            # Insert into Snowflake
            success, msg = snowflake_vector_service.insert_product(product, vector)
            
            if success:
                print(f"  -> Inserted successfully.")
                success_count += 1
            else:
                print(f"  -> Insert failed: {msg}")
                
            # Rate limit slightly to be nice to APIs
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  -> Error processing {product_name}: {e}")

    print(f"\nSeeding Complete! Successfully inserted {success_count}/{len(SAMPLE_PRODUCTS)} products.")

if __name__ == "__main__":
    seed_products()
