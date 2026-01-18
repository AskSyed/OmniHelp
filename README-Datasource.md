# Data Source Guide for RAG Application

This document provides comprehensive guidance on datasets suitable for the RAG (Retrieval-Augmented Generation) application, focusing on product catalogs with prices, descriptions, and technical specifications.

## Overview

The RAG system supports both **PDF** and **CSV** formats for document ingestion. This guide recommends datasets that enable rich product queries including:
- Product descriptions and specifications
- Pricing information
- Technical manuals and documentation
- Category and taxonomy data
- Brand and manufacturer details

## Top Recommended Datasets

### 1. Shopify Product Catalogue Dataset ⭐ (Recommended)

**Source:** Hugging Face - `Shopify/product-catalogue`  
**Size:** ~48,289 products  
**Format:** CSV/JSON  
**License:** Publicly available

**Key Fields:**
- Product titles
- Descriptions
- Brand information
- Hierarchical categories
- Product images (URLs)

**Why It's Ideal:**
- Real-world e-commerce data
- Rich textual descriptions perfect for RAG
- Well-structured category taxonomy
- Ready for CSV ingestion
- High-quality, curated dataset

**Download:**
```bash
pip install datasets
python -c "from datasets import load_dataset; ds = load_dataset('Shopify/product-catalogue'); ds['train'].to_pandas().to_csv('products.csv', index=False)"
```

**Direct Link:** https://huggingface.co/datasets/Shopify/product-catalogue

---

### 2. Amazon Product Listing Dataset

**Source:** OpenDataBay / Kaggle  
**Size:** ~700,000 products (2020 snapshot)  
**Format:** CSV  
**License:** Varies by source

**Key Fields:**
- Product name
- Brand
- ASIN (Amazon Standard Identification Number)
- Category
- Product description
- Variants information

**Why It's Useful:**
- Large scale for comprehensive coverage
- Includes detailed product descriptions
- Good for price and feature comparison queries
- Multiple product categories

**Note:** Data is from 2020, but excellent for testing and development

**Download:** Available on Kaggle and OpenDataBay

---

### 3. E-commerce Dataset (Yujiangw)

**Source:** Hugging Face - `yujiangw/E-commerce`  
**Size:** ~8,000 samples  
**Format:** Multiple formats available  
**License:** Public

**Key Fields:**
- Product attributes
- Categories
- Descriptions
- Structured metadata

**Why It's Useful:**
- Lightweight for quick testing
- Clean, well-structured data
- Perfect for development and prototyping
- Multiple train/test splits available

**Download:**
```bash
pip install datasets
python -c "from datasets import load_dataset; ds = load_dataset('yujiangw/E-commerce')"
```

**Direct Link:** https://huggingface.co/datasets/yujiangw/E-commerce

---

### 4. Walmart Product Price Data

**Source:** OpenDataBay  
**Size:** ~30,000 products  
**Format:** CSV  
**License:** Public

**Key Fields:**
- Product prices
- Reviews and ratings
- Category information
- Product details

**Why It's Useful:**
- Includes pricing information (often missing in other datasets)
- Real retail data
- Useful for price comparison queries
- Complementary to other product datasets

**Use Case:** Best used in combination with other datasets to add pricing dimension

---

## Recommended Dataset Combinations

### Option A: Quick Start (Development/Testing)

**Best for:** Initial development, testing, and prototyping

```
1. Shopify Product Catalogue (CSV)
   - Primary dataset
   - Rich descriptions
   - ~48K products

2. E-commerce Dataset (yujiangw)
   - Secondary dataset
   - Clean structure
   - ~8K products
```

**Total Coverage:** ~56,000 products  
**Setup Time:** < 1 hour  
**Best For:** Testing RAG queries, development, demos

---

### Option B: Production-Ready (Large Scale)

**Best for:** Production deployments, comprehensive product knowledge base

```
1. Amazon Product Listing Data (CSV)
   - Large scale (700K products)
   - Comprehensive metadata

2. Walmart Price Data (CSV)
   - Pricing information
   - Complementary pricing data

3. Custom PDF Manuals
   - Technical specifications
   - Product manuals (e.g., Dell Latitude 3480)
   - User guides
```

**Total Coverage:** 700K+ products + technical documentation  
**Setup Time:** 2-4 hours  
**Best For:** Production systems, enterprise deployments

---

## CSV Dataset Structure

For optimal RAG performance, your CSV should include the following columns:

### Required Fields
- `product_id` - Unique identifier
- `product_name` - Product title/name
- `description` - Detailed product description (most important for RAG)
- `category` - Product category

### Recommended Fields
- `brand` - Manufacturer/brand name
- `price` - Product price
- `specifications` - Technical specs (JSON string or delimited)
- `features` - Key features (comma-separated or JSON)
- `stock_status` - Availability information
- `image_url` - Product image URL (optional)

### Example CSV Structure

```csv
product_id,product_name,brand,category,description,price,specifications,features,stock_status
PROD001,Latitude 3480 Laptop,Dell,Electronics,"High-performance business laptop with Intel Core i5 processor, 8GB RAM, and 256GB SSD storage. Perfect for professionals.",899.99,"Processor: Intel i5-7200U|RAM: 8GB|Storage: 256GB SSD|Display: 14 inch","Backlit keyboard, Fingerprint reader, Long battery life",In Stock
PROD002,Wireless Mouse,Logitech,Accessories,"Ergonomic wireless mouse with 2.4GHz connectivity and 12-month battery life.",29.99,"Connectivity: 2.4GHz|Battery: 12 months|DPI: 1000","Ergonomic design, Silent clicking, USB receiver included",In Stock
```

---

## PDF Manual Sources

For technical product documentation in PDF format:

### 1. Manufacturer Websites
- **Dell:** https://www.dell.com/support/manuals
- **HP:** https://support.hp.com/documentation
- **Lenovo:** https://support.lenovo.com/manuals

### 2. Sample Manuals
- **Dell Latitude 3480 Owner's Manual:** 
  https://dl.dell.com/content/manual34122770-latitude-3480-owner-s-manual.pdf?language=en-us

### 3. Creating Custom PDFs
You can generate PDFs from product data using Python:

```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def create_product_manual(product_data):
    """Generate a PDF manual from product data"""
    filename = f"{product_data['product_id']}_manual.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    
    # Add product information
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, 10*inch, product_data['product_name'])
    
    c.setFont("Helvetica", 12)
    y = 9.5*inch
    c.drawString(1*inch, y, f"Brand: {product_data['brand']}")
    y -= 0.3*inch
    c.drawString(1*inch, y, f"Price: ${product_data['price']}")
    y -= 0.5*inch
    
    # Add description
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1*inch, y, "Description:")
    y -= 0.3*inch
    c.setFont("Helvetica", 11)
    # Wrap text for description
    lines = product_data['description'].split('. ')
    for line in lines:
        c.drawString(1*inch, y, line)
        y -= 0.25*inch
    
    c.save()
    return filename
```

---

## Data Preparation Steps

### Step 1: Download Dataset

```bash
# For Shopify dataset
pip install datasets
python download_shopify.py

# Or manually download from Hugging Face
```

### Step 2: Clean and Normalize

```python
import pandas as pd

# Load dataset
df = pd.read_csv('products.csv')

# Clean data
df = df.dropna(subset=['description', 'product_name'])
df['description'] = df['description'].str.strip()
df['price'] = pd.to_numeric(df['price'], errors='coerce')

# Normalize categories
df['category'] = df['category'].str.lower().str.strip()

# Save cleaned data
df.to_csv('products_cleaned.csv', index=False)
```

### Step 3: Enhance with Pricing (if missing)

```python
# Merge with pricing dataset
pricing_df = pd.read_csv('walmart_prices.csv')
df = df.merge(pricing_df[['product_id', 'price']], 
              on='product_id', 
              how='left', 
              suffixes=('', '_walmart'))

# Use Walmart price if original price missing
df['price'] = df['price'].fillna(df['price_walmart'])
```

### Step 4: Prepare for Ingestion

```python
# Ensure all required fields are present
required_fields = ['product_id', 'product_name', 'description', 'category']
assert all(field in df.columns for field in required_fields)

# Create rich text chunks for better RAG
df['rag_text'] = (
    df['product_name'] + '. ' +
    df['description'] + '. ' +
    'Category: ' + df['category'].astype(str) + '. ' +
    'Brand: ' + df['brand'].fillna('Unknown').astype(str) + '. ' +
    'Price: $' + df['price'].astype(str)
)

# Save for ingestion
df.to_csv('products_rag_ready.csv', index=False)
```

---

## Domain-Specific Recommendations

### Electronics & Technology Products
- **Primary:** Amazon Electronics listings
- **Secondary:** Manufacturer PDF manuals (Dell, HP, Lenovo)
- **Enhancement:** Technical specification sheets

### Fashion & Apparel
- **Primary:** Fashion Product Images dataset
- **Fields:** Size charts, material information, style descriptions

### Home & Kitchen
- **Primary:** Amazon Home & Kitchen category
- **Secondary:** Product manuals and care instructions (PDFs)

### General E-commerce
- **Primary:** Shopify Product Catalogue
- **Secondary:** Amazon listings for breadth
- **Enhancement:** Walmart pricing data

---

## Upload Instructions

### CSV Upload

1. Prepare your CSV file with the recommended structure
2. Use the API endpoint:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/documents/upload" \
     -F "file=@products.csv"
   ```
3. The system will:
   - Parse each row as a text chunk
   - Generate embeddings
   - Store in ChromaDB with metadata

### PDF Upload

1. Collect product manuals in PDF format
2. Use the API endpoint:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/documents/upload" \
     -F "file=@product_manual.pdf"
   ```
3. The system will:
   - Extract text from PDF
   - Chunk the text
   - Generate embeddings
   - Store in ChromaDB

---

## Query Examples

Once your data is ingested, you can query:

### Price Queries
- "What products are available under $500?"
- "Show me the cheapest laptops"
- "What's the price range for wireless mice?"

### Feature Queries
- "Show me laptops with 8GB RAM"
- "What products have fingerprint readers?"
- "Find products with backlit keyboards"

### Category Queries
- "What electronics products do you have?"
- "Show me all Dell products"
- "What accessories are in stock?"

### Specification Queries
- "What are the specifications of [product name]?"
- "Compare features between product A and B"
- "What's the battery life of this laptop?"

---

## Data Quality Best Practices

1. **Rich Descriptions:** Ensure product descriptions are detailed (100+ words ideal)
2. **Consistent Formatting:** Normalize categories, brands, and specifications
3. **Complete Metadata:** Include all available fields for better filtering
4. **Price Accuracy:** Keep pricing data current if possible
5. **Regular Updates:** Refresh data periodically for accuracy

---

## Troubleshooting

### Issue: Poor Query Results
**Solution:** Ensure descriptions are rich and detailed. Add more context to product entries.

### Issue: Missing Prices
**Solution:** Merge with pricing datasets or use synthetic pricing based on categories.

### Issue: PDF Parsing Errors
**Solution:** Ensure PDFs are text-based (not scanned images). Use OCR if needed.

### Issue: Category Mismatches
**Solution:** Normalize categories across datasets before ingestion.

---

## Additional Resources

- **Hugging Face Datasets:** https://huggingface.co/datasets
- **Kaggle Datasets:** https://www.kaggle.com/datasets
- **OpenDataBay:** https://www.opendatabay.com
- **Langchain Document Loaders:** https://python.langchain.com/docs/modules/data_connection/document_loaders/

---

## Support

For questions about data preparation or ingestion:
1. Check the main README.md for API documentation
2. Review the document service code in `app/services/document_service.py`
3. Test with small datasets first before full ingestion

---

**Last Updated:** 2024  
**Maintained By:** RAG Application Team
