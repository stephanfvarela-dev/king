"""
Printify African Designs Automation Script
Author: King (stephanfvarela-dev)
Description:
    - Uploads your African design/logo to Printify
    - Automatically discovers all available product types (shirts, mugs, hoodies, etc.)
    - Publishes each product with Africa-inspired branding and descriptions in your Printify store
"""

import os
import requests
import logging
from typing import List, Dict, Any

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

API_URL = "https://api.printify.com/v1"
API_KEY = os.getenv("PRINTIFY_API_KEY")
STORE_ID = os.getenv("PRINTIFY_STORE_ID")
LOGO_PATH = os.getenv("LOGO_PATH", "fc_cabo_verde_logo.png")

HEADERS = {"Authorization": f"Bearer {API_KEY}"}

def ensure_config():
    if not API_KEY or not STORE_ID:
        logging.error("Set PRINTIFY_API_KEY and PRINTIFY_STORE_ID as environment variables.")
        exit(1)

def upload_logo(image_path: str) -> str:
    logging.info("Uploading your African design logo to Printify...")
    url = f"{API_URL}/uploads/images.json"
    with open(image_path, 'rb') as img_file:
        files = {"file": img_file}
        resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}"}, files=files)
    resp.raise_for_status()
    image_id = resp.json()["id"]
    logging.info(f"Logo uploaded, image ID: {image_id}")
    return image_id

def fetch_blueprints() -> List[Dict[str, Any]]:
    logging.info("Fetching all available product blueprints from Printify...")
    url = f"{API_URL}/catalog/blueprints.json"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    blueprints = resp.json()
    logging.info(f"Found {len(blueprints)} blueprints.")
    return blueprints

def fetch_print_providers(blueprint_id: int) -> List[Dict[str, Any]]:
    url = f"{API_URL}/catalog/blueprints/{blueprint_id}/print_providers.json"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def fetch_variants(blueprint_id: int, provider_id: int) -> List[Dict[str, Any]]:
    url = f"{API_URL}/catalog/blueprints/{blueprint_id}/print_providers/{provider_id}/variants.json"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def create_and_publish_product(blueprint, provider, variants, image_id):
    # Professional, Africa-inspired branding
    title = f"{blueprint['name']} – African Heritage Series"
    desc = (
        f"Celebrate African pride and culture with this exclusive '{blueprint['name']}' featuring the iconic FC Cabo Verde logo. "
        "Perfect for supporters of African design and football heritage."
    )
    variant_ids = [v["id"] for v in variants][:2]
    variant_data = [{"id": vid, "price": 2500, "is_enabled": True} for vid in variant_ids]
    print_area_position = variants[0]["print_areas"][0]["position"] if variants and "print_areas" in variants[0] else "front"
    print_areas = [{
        "variant_ids": variant_ids,
        "placeholders": [{
            "position": print_area_position,
            "images": [{
                "id": image_id,
                "x": 0.5,
                "y": 0.5,
                "scale": 1.0,
                "angle": 0
            }]
        }]
    }]
    product_data = {
        "title": title,
        "description": desc,
        "blueprint_id": blueprint["id"],
        "print_provider_id": provider["id"],
        "variants": variant_data,
        "print_areas": print_areas
    }
    url = f"{API_URL}/shops/{STORE_ID}/products.json"
    resp = requests.post(url, headers={**HEADERS, "Content-Type": "application/json"}, json=product_data)
    resp.raise_for_status()
    product_id = resp.json()["id"]
    logging.info(f"Created product: {title} (ID: {product_id})")
    # Publish
    url = f"{API_URL}/shops/{STORE_ID}/products/{product_id}/publish.json"
    publish_data = {"title": True, "description": True, "images": True, "variants": True, "tags": True}
    pub_resp = requests.post(url, headers={**HEADERS, "Content-Type": "application/json"}, json=publish_data)
    pub_resp.raise_for_status()
    logging.info(f"Published product: {title}")

def main():
    ensure_config()
    image_id = upload_logo(LOGO_PATH)
    blueprints = fetch_blueprints()
    for blueprint in blueprints:
        try:
            providers = fetch_print_providers(blueprint["id"])
            if not providers:
                logging.warning(f"No providers for blueprint: {blueprint['name']}")
                continue
            provider = providers[0]
            variants = fetch_variants(blueprint["id"], provider["id"])
            if not variants:
                logging.warning(f"No variants for provider {provider['id']} of blueprint {blueprint['name']}")
                continue
            create_and_publish_product(blueprint, provider, variants, image_id)
        except Exception as e:
            logging.error(f"Failed for {blueprint['name']}: {e}")

if __name__ == "__main__":
    main()