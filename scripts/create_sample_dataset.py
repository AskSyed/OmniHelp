"""
Create a sample product dataset for testing RAG application
"""
import pandas as pd
import random
from pathlib import Path
from datetime import datetime


def generate_sample_dataset(
    num_products: int = 100,
    output_path: str = "data/sample/products_sample.csv"
):
    """
    Generate a sample product dataset with realistic data
    
    Args:
        num_products: Number of products to generate
        output_path: Path to save the CSV file
    """
    print(f"Generating sample dataset with {num_products} products...")
    
    # Product categories
    categories = [
        "Electronics", "Laptops", "Smartphones", "Tablets",
        "Accessories", "Headphones", "Keyboards", "Mice",
        "Monitors", "Printers", "Cameras", "Smart Home"
    ]
    
    # Brands
    brands = {
        "Electronics": ["Dell", "HP", "Lenovo", "Apple", "Samsung"],
        "Laptops": ["Dell", "HP", "Lenovo", "Apple", "ASUS"],
        "Smartphones": ["Apple", "Samsung", "Google", "OnePlus", "Xiaomi"],
        "Tablets": ["Apple", "Samsung", "Microsoft", "Amazon"],
        "Accessories": ["Logitech", "Anker", "Belkin", "Sony"],
        "Headphones": ["Sony", "Bose", "Sennheiser", "JBL"],
        "Keyboards": ["Logitech", "Corsair", "Razer", "Keychron"],
        "Mice": ["Logitech", "Razer", "Corsair", "SteelSeries"],
        "Monitors": ["Dell", "LG", "Samsung", "ASUS"],
        "Printers": ["HP", "Canon", "Epson", "Brother"],
        "Cameras": ["Canon", "Nikon", "Sony", "Fujifilm"],
        "Smart Home": ["Amazon", "Google", "Philips", "Ring"]
    }
    
    # Product templates
    product_templates = {
        "Laptops": [
            ("{brand} {model} Laptop", "High-performance {category_lower} with Intel Core i{processor} processor, {ram}GB RAM, and {storage}GB SSD storage. Perfect for {use_case}."),
            ("{brand} {model} Notebook", "Business-class {category_lower} featuring {ram}GB memory, {storage}GB storage, and {display} inch display. Ideal for professionals."),
        ],
        "Smartphones": [
            ("{brand} {model} Smartphone", "Latest {category_lower} with {ram}GB RAM, {storage}GB storage, and {camera}MP camera. Features {display} inch display and long battery life."),
        ],
        "Accessories": [
            ("{brand} {product_type}", "Premium {category_lower} with {features}. Designed for {use_case}."),
        ],
        "Electronics": [
            ("{brand} {model} {product_type}", "Advanced {category_lower} with cutting-edge features including {features}. Perfect for {use_case}."),
        ]
    }
    
    products = []
    
    for i in range(num_products):
        category = random.choice(categories)
        brand = random.choice(brands.get(category, brands["Electronics"]))
        
        # Generate product details
        model = f"{random.choice(['Pro', 'Elite', 'Standard', 'Premium', 'Ultra'])} {random.randint(1000, 9999)}"
        processor = random.choice([5, 7, 9])
        ram = random.choice([4, 8, 16, 32])
        storage = random.choice([128, 256, 512, 1024])
        display = random.choice([13.3, 14, 15.6, 17.3, 24, 27])
        camera = random.choice([12, 16, 24, 48, 64])
        
        # Generate price based on category and specs
        base_price = {
            "Laptops": 600 + (ram * 20) + (storage * 0.5),
            "Smartphones": 300 + (ram * 15) + (storage * 0.3),
            "Tablets": 200 + (storage * 0.4),
            "Accessories": 20 + random.randint(0, 100),
            "Headphones": 50 + random.randint(0, 300),
            "Keyboards": 30 + random.randint(0, 200),
            "Mice": 15 + random.randint(0, 100),
            "Monitors": 150 + random.randint(0, 500),
            "Printers": 80 + random.randint(0, 400),
            "Cameras": 300 + random.randint(0, 2000),
            "Smart Home": 50 + random.randint(0, 300),
            "Electronics": 100 + random.randint(0, 500)
        }
        price = round(base_price.get(category, 100) + random.uniform(-50, 50), 2)
        
        # Generate product name and description
        product_type = category.lower() if category != "Electronics" else random.choice(["Device", "System", "Unit"])
        use_case = random.choice(["professional use", "gaming", "home office", "creative work", "everyday computing"])
        features = random.choice([
            "wireless connectivity, long battery life",
            "fast processing, high-resolution display",
            "sleek design, premium materials",
            "advanced features, user-friendly interface"
        ])
        
        # Get template
        templates = product_templates.get(category, product_templates["Electronics"])
        name_template, desc_template = random.choice(templates)
        
        product_name = name_template.format(
            brand=brand,
            model=model,
            product_type=product_type
        )
        
        description = desc_template.format(
            brand=brand,
            model=model,
            category=category,
            category_lower=category.lower(),
            processor=processor,
            ram=ram,
            storage=storage,
            display=display,
            camera=camera,
            product_type=product_type,
            use_case=use_case,
            features=features
        )
        
        # Generate specifications
        specs = f"Processor: Intel Core i{processor}|RAM: {ram}GB|Storage: {storage}GB|Display: {display} inch"
        if category == "Smartphones":
            specs += f"|Camera: {camera}MP"
        
        # Generate features
        feature_list = [
            "High performance",
            "Long battery life",
            "Premium design",
            "Fast connectivity"
        ]
        if category in ["Laptops", "Smartphones"]:
            feature_list.extend(["Fingerprint reader", "Backlit keyboard"])
        features_str = ", ".join(random.sample(feature_list, k=min(3, len(feature_list))))
        
        # Stock status
        stock_status = random.choice(["In Stock", "Low Stock", "Out of Stock"])
        
        products.append({
            "product_id": f"PROD{str(i+1).zfill(6)}",
            "product_name": product_name,
            "brand": brand,
            "category": category,
            "description": description,
            "price": price,
            "specifications": specs,
            "features": features_str,
            "stock_status": stock_status,
            "created_date": datetime.now().strftime("%Y-%m-%d")
        })
    
    # Create DataFrame
    df = pd.DataFrame(products)
    
    # Add RAG text column
    df['rag_text'] = (
        df['product_name'] + '. ' +
        df['description'] + '. ' +
        'Category: ' + df['category'] + '. ' +
        'Brand: ' + df['brand'] + '. ' +
        'Price: $' + df['price'].astype(str) + '. ' +
        'Specifications: ' + df['specifications'] + '. ' +
        'Features: ' + df['features'] + '. ' +
        'Stock Status: ' + df['stock_status']
    )
    
    # Save to CSV
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print(f"✓ Generated {len(df)} products")
    print(f"✓ Saved to: {output_path}")
    print(f"\nDataset Statistics:")
    print(f"  Categories: {df['category'].nunique()}")
    print(f"  Brands: {df['brand'].nunique()}")
    print(f"  Price range: ${df['price'].min():.2f} - ${df['price'].max():.2f}")
    print(f"  Average price: ${df['price'].mean():.2f}")
    
    return df


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate sample product dataset")
    parser.add_argument(
        "-n", "--num-products",
        type=int,
        default=100,
        help="Number of products to generate (default: 100)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="data/sample/products_sample.csv",
        help="Output CSV file path"
    )
    
    args = parser.parse_args()
    
    generate_sample_dataset(
        num_products=args.num_products,
        output_path=args.output
    )
