"""
Prepare and clean CSV datasets for RAG ingestion
"""
import pandas as pd
import sys
from pathlib import Path
import json


def clean_and_normalize_csv(
    input_path: str,
    output_path: str,
    required_fields: list = None,
    add_rag_text: bool = True
):
    """
    Clean and normalize CSV data for RAG ingestion
    
    Args:
        input_path: Path to input CSV file
        output_path: Path to save cleaned CSV
        required_fields: List of required field names
        add_rag_text: Whether to add a combined RAG text column
    """
    print(f"Loading CSV from: {input_path}")
    
    try:
        df = pd.read_csv(input_path)
        print(f"✓ Loaded {len(df)} rows, {len(df.columns)} columns")
        
        # Default required fields
        if required_fields is None:
            required_fields = ['product_name', 'description']
        
        # Check for required fields
        missing_fields = [f for f in required_fields if f not in df.columns]
        if missing_fields:
            print(f"⚠ Warning: Missing fields: {', '.join(missing_fields)}")
            print(f"Available columns: {', '.join(df.columns.tolist())}")
        
        # Clean data
        print("\nCleaning data...")
        
        # Remove rows with missing required fields
        initial_count = len(df)
        for field in required_fields:
            if field in df.columns:
                df = df.dropna(subset=[field])
        removed = initial_count - len(df)
        if removed > 0:
            print(f"✓ Removed {removed} rows with missing required fields")
        
        # Clean text fields
        text_fields = ['product_name', 'description', 'title', 'name']
        for field in text_fields:
            if field in df.columns:
                df[field] = df[field].astype(str).str.strip()
                df[field] = df[field].replace('nan', '')
        
        # Normalize categories
        if 'category' in df.columns:
            df['category'] = df['category'].astype(str).str.lower().str.strip()
            print(f"✓ Normalized categories: {df['category'].nunique()} unique categories")
        
        # Clean price field if exists
        if 'price' in df.columns:
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            print(f"✓ Cleaned price field: {df['price'].notna().sum()} valid prices")
        
        # Add RAG text column if requested
        if add_rag_text:
            print("\nCreating RAG text column...")
            df = create_rag_text_column(df)
            print("✓ Created RAG text column")
        
        # Save cleaned data
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        
        print(f"\n✓ Saved cleaned data to: {output_path}")
        print(f"✓ Final dataset: {len(df)} rows, {len(df.columns)} columns")
        
        return df
    
    except Exception as e:
        print(f"Error processing CSV: {e}")
        raise


def create_rag_text_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a rich text column optimized for RAG
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with 'rag_text' column added
    """
    rag_parts = []
    
    # Add product name/title
    if 'product_name' in df.columns:
        rag_parts.append(df['product_name'].fillna(''))
    elif 'title' in df.columns:
        rag_parts.append(df['title'].fillna(''))
    elif 'name' in df.columns:
        rag_parts.append(df['name'].fillna(''))
    
    # Add description
    if 'description' in df.columns:
        rag_parts.append(df['description'].fillna(''))
    
    # Add category
    if 'category' in df.columns:
        rag_parts.append('Category: ' + df['category'].fillna('Unknown').astype(str))
    
    # Add brand
    if 'brand' in df.columns:
        rag_parts.append('Brand: ' + df['brand'].fillna('Unknown').astype(str))
    
    # Add price
    if 'price' in df.columns:
        price_text = df['price'].apply(
            lambda x: f'Price: ${x:.2f}' if pd.notna(x) else 'Price: Not available'
        )
        rag_parts.append(price_text)
    
    # Add specifications if exists
    if 'specifications' in df.columns:
        rag_parts.append('Specifications: ' + df['specifications'].fillna('').astype(str))
    
    # Add features if exists
    if 'features' in df.columns:
        rag_parts.append('Features: ' + df['features'].fillna('').astype(str))
    
    # Combine all parts
    df['rag_text'] = '. '.join(rag_parts)
    
    # Clean up the rag_text
    df['rag_text'] = df['rag_text'].str.replace('\.\.+', '.', regex=True)  # Remove multiple dots
    df['rag_text'] = df['rag_text'].str.strip()
    
    return df


def merge_datasets(
    dataset_paths: list,
    output_path: str,
    merge_key: str = None
):
    """
    Merge multiple CSV datasets
    
    Args:
        dataset_paths: List of paths to CSV files
        output_path: Path to save merged CSV
        merge_key: Key column for merging (if None, concatenates)
    """
    print(f"Merging {len(dataset_paths)} datasets...")
    
    dataframes = []
    for path in dataset_paths:
        print(f"  Loading: {path}")
        df = pd.read_csv(path)
        dataframes.append(df)
        print(f"    ✓ {len(df)} rows")
    
    if merge_key and all(merge_key in df.columns for df in dataframes):
        # Merge on common key
        merged = dataframes[0]
        for df in dataframes[1:]:
            merged = merged.merge(df, on=merge_key, how='outer', suffixes=('', '_dup'))
        print(f"✓ Merged on key: {merge_key}")
    else:
        # Concatenate
        merged = pd.concat(dataframes, ignore_index=True)
        print("✓ Concatenated datasets")
    
    # Remove duplicate columns
    merged = merged.loc[:, ~merged.columns.str.endswith('_dup')]
    
    # Save
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_path, index=False)
    
    print(f"✓ Saved merged dataset to: {output_path}")
    print(f"✓ Total rows: {len(merged)}")
    
    return merged


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Prepare CSV data for RAG ingestion")
    parser.add_argument(
        "input",
        type=str,
        help="Input CSV file path"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output CSV file path (default: adds '_cleaned' to input name)"
    )
    parser.add_argument(
        "--no-rag-text",
        action="store_true",
        help="Don't add RAG text column"
    )
    parser.add_argument(
        "--required-fields",
        type=str,
        nargs="+",
        default=["product_name", "description"],
        help="Required fields (default: product_name description)"
    )
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output is None:
        input_path = Path(args.input)
        output_path = input_path.parent / f"{input_path.stem}_cleaned{input_path.suffix}"
    else:
        output_path = args.output
    
    clean_and_normalize_csv(
        input_path=args.input,
        output_path=str(output_path),
        required_fields=args.required_fields,
        add_rag_text=not args.no_rag_text
    )
