"""
Download datasets from various sources for RAG application
"""
import os
import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path for imports if needed
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from datasets import load_dataset
except ImportError:
    print("Error: 'datasets' library not found. Install it with: pip install datasets")
    sys.exit(1)


def download_shopify_dataset(output_dir: str = "data/raw"):
    """
    Download Shopify Product Catalogue dataset from Hugging Face
    
    Args:
        output_dir: Directory to save the dataset
    """
    print("Downloading Shopify Product Catalogue dataset...")
    
    try:
        # Load dataset from Hugging Face
        dataset = load_dataset("Shopify/product-catalogue")
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Convert to pandas DataFrame
        if 'train' in dataset:
            df = dataset['train'].to_pandas()
        else:
            df = dataset.to_pandas()
        
        # Save as CSV
        output_path = Path(output_dir) / "shopify_products.csv"
        df.to_csv(output_path, index=False)
        
        print(f"✓ Downloaded {len(df)} products")
        print(f"✓ Saved to: {output_path}")
        print(f"✓ Columns: {', '.join(df.columns.tolist())}")
        
        return str(output_path)
    
    except Exception as e:
        print(f"Error downloading Shopify dataset: {e}")
        return None


def download_ecommerce_dataset(output_dir: str = "data/raw"):
    """
    Download E-commerce dataset from Hugging Face (yujiangw)
    
    Args:
        output_dir: Directory to save the dataset
    """
    print("Downloading E-commerce dataset (yujiangw)...")
    
    try:
        # Load dataset from Hugging Face
        dataset = load_dataset("yujiangw/E-commerce")
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Convert to pandas DataFrame
        if 'train' in dataset:
            df = dataset['train'].to_pandas()
        elif 'default' in dataset:
            df = dataset['default'].to_pandas()
        else:
            df = list(dataset.values())[0].to_pandas()
        
        # Save as CSV
        output_path = Path(output_dir) / "ecommerce_products.csv"
        df.to_csv(output_path, index=False)
        
        print(f"✓ Downloaded {len(df)} products")
        print(f"✓ Saved to: {output_path}")
        print(f"✓ Columns: {', '.join(df.columns.tolist())}")
        
        return str(output_path)
    
    except Exception as e:
        print(f"Error downloading E-commerce dataset: {e}")
        return None


def download_all_datasets(output_dir: str = "data/raw"):
    """
    Download all available datasets
    
    Args:
        output_dir: Directory to save the datasets
    """
    print("=" * 60)
    print("Downloading all datasets for RAG application")
    print("=" * 60)
    
    results = {}
    
    # Download Shopify dataset
    print("\n[1/2] Shopify Product Catalogue")
    results['shopify'] = download_shopify_dataset(output_dir)
    
    # Download E-commerce dataset
    print("\n[2/2] E-commerce Dataset (yujiangw)")
    results['ecommerce'] = download_ecommerce_dataset(output_dir)
    
    print("\n" + "=" * 60)
    print("Download Summary:")
    print("=" * 60)
    for name, path in results.items():
        if path:
            print(f"✓ {name}: {path}")
        else:
            print(f"✗ {name}: Failed to download")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Download datasets for RAG application")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw",
        help="Output directory for downloaded datasets (default: data/raw)"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        choices=["shopify", "ecommerce", "all"],
        default="all",
        help="Dataset to download (default: all)"
    )
    
    args = parser.parse_args()
    
    if args.dataset == "shopify":
        download_shopify_dataset(args.output_dir)
    elif args.dataset == "ecommerce":
        download_ecommerce_dataset(args.output_dir)
    else:
        download_all_datasets(args.output_dir)
