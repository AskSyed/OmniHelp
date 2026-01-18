# Data Preparation Scripts

This directory contains helper scripts for downloading and preparing datasets for the RAG application. These scripts can be executed independently without affecting other parts of the project.

## Setup

Install the required dependencies:

```bash
pip install -r scripts/requirements_scripts.txt
```

Or install individually:

```bash
pip install datasets pandas
```

## Scripts Overview

### 1. `download_datasets.py`

Downloads datasets from Hugging Face and other sources.

**Usage:**

```bash
# Download all available datasets
python scripts/download_datasets.py

# Download specific dataset
python scripts/download_datasets.py --dataset shopify
python scripts/download_datasets.py --dataset ecommerce

# Specify output directory
python scripts/download_datasets.py --output-dir data/raw
```

**Available datasets:**
- `shopify` - Shopify Product Catalogue (~48K products)
- `ecommerce` - E-commerce dataset from yujiangw (~8K products)
- `all` - Download all datasets (default)

**Output:** Datasets are saved to `data/raw/` by default.

---

### 2. `prepare_csv_data.py`

Cleans and normalizes CSV data for RAG ingestion.

**Usage:**

```bash
# Basic usage
python scripts/prepare_csv_data.py data/raw/shopify_products.csv

# Specify output file
python scripts/prepare_csv_data.py data/raw/shopify_products.csv -o data/cleaned/products_cleaned.csv

# Custom required fields
python scripts/prepare_csv_data.py data/raw/products.csv --required-fields product_name description price

# Don't add RAG text column
python scripts/prepare_csv_data.py data/raw/products.csv --no-rag-text
```

**Features:**
- Removes rows with missing required fields
- Normalizes text fields (strips whitespace)
- Normalizes categories (lowercase, trimmed)
- Cleans price fields (converts to numeric)
- Creates optimized RAG text column
- Handles multiple CSV formats

**Output:** Cleaned CSV file (default: adds `_cleaned` suffix)

---

### 3. `create_sample_dataset.py`

Generates a sample product dataset for testing.

**Usage:**

```bash
# Generate 100 products (default)
python scripts/create_sample_dataset.py

# Generate specific number of products
python scripts/create_sample_dataset.py -n 500

# Specify output file
python scripts/create_sample_dataset.py -o data/sample/my_products.csv
```

**Features:**
- Generates realistic product data
- Multiple categories (Electronics, Laptops, Smartphones, etc.)
- Includes prices, descriptions, specifications
- Creates RAG-optimized text column
- Perfect for testing and development

**Output:** Sample CSV file at `data/sample/products_sample.csv`

---

## Complete Workflow Example

### Option 1: Download and Prepare Real Datasets

```bash
# Step 1: Download datasets
python scripts/download_datasets.py --dataset shopify

# Step 2: Clean and prepare
python scripts/prepare_csv_data.py data/raw/shopify_products.csv -o data/ready/shopify_ready.csv

# Step 3: Upload to RAG system
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@data/ready/shopify_ready.csv"
```

### Option 2: Generate Sample Dataset for Testing

```bash
# Generate sample dataset
python scripts/create_sample_dataset.py -n 200 -o data/sample/test_products.csv

# Upload to RAG system
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@data/sample/test_products.csv"
```

---

## Directory Structure

After running scripts, your data directory will look like:

```
data/
├── raw/                    # Raw downloaded datasets
│   ├── shopify_products.csv
│   └── ecommerce_products.csv
├── cleaned/                # Cleaned and normalized datasets
│   ├── shopify_products_cleaned.csv
│   └── ecommerce_products_cleaned.csv
└── sample/                 # Sample/test datasets
    └── products_sample.csv
```

---

## Script Functions Reference

### `download_datasets.py`

- `download_shopify_dataset(output_dir)` - Download Shopify dataset
- `download_ecommerce_dataset(output_dir)` - Download E-commerce dataset
- `download_all_datasets(output_dir)` - Download all datasets

### `prepare_csv_data.py`

- `clean_and_normalize_csv(input_path, output_path, ...)` - Clean CSV data
- `create_rag_text_column(df)` - Create RAG-optimized text column
- `merge_datasets(dataset_paths, output_path)` - Merge multiple CSVs

### `create_sample_dataset.py`

- `generate_sample_dataset(num_products, output_path)` - Generate sample data

---

## Troubleshooting

### Issue: "datasets library not found"
**Solution:** Install dependencies: `pip install -r scripts/requirements_scripts.txt`

### Issue: "File not found" errors
**Solution:** Ensure data directories exist or scripts will create them automatically

### Issue: Memory errors with large datasets
**Solution:** Process datasets in chunks or use a machine with more RAM

### Issue: Download fails
**Solution:** Check internet connection and Hugging Face access. Some datasets may require authentication.

---

## Integration with RAG System

After preparing your datasets:

1. **Upload CSV:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/documents/upload" \
     -F "file=@data/ready/products.csv"
   ```

2. **Query the system:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "What products are available under $500?"}'
   ```

---

## Notes

- Scripts are designed to be run independently
- They don't modify the main application code
- All outputs go to `data/` directory (gitignored)
- Scripts can be run multiple times safely (will overwrite existing files)

---

**For more information on datasets, see:** `README-Datasource.md` in project root.
