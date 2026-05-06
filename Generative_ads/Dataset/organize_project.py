"""
organize_project.py
===================
Script to organize the AI project repository for the advertisement creative intelligence merging.
Restructures into a clean ML repository and exports an integration package for both pipelines.
"""

import os
import shutil
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TARGET_PROJECT_DIR = os.path.join(BASE_DIR, "generative_ads_ai")
INTEGRATION_DIR = os.path.join(BASE_DIR, "integration_package")

# Define the directory structure to create
DIRECTORY_STRUCTURE = [
    "data/company_ads",
    "data/competitor_ads",
    "data/images/company_images",
    "data/images/competitor_images",
    "models",
    "src/feature_extraction",
    "src/modeling",
    "src/evaluation",
    "src/integration",
    "reports",
    "archive"
]

# Define source paths (assuming they exist in the current BASE_DIR or its subdirectories)
FILE_MAPPINGS = {
    # Company Ads Data
    "ads_dataset_filtered.csv": "data/company_ads",
    "ads_features.csv": "data/company_ads",
    "creative_ranked_ads.csv": "data/company_ads",
    
    # Competitor Ads Data
    "competitor_features.csv": "data/competitor_ads",
    "layout_clusters.csv": "data/competitor_ads",
    "cluster_summary.csv": "data/competitor_ads",
    "cluster_descriptions.csv": "data/competitor_ads",
    
    # Models
    "creative_performance_model.pkl": "models",
    "ctr_model.pkl": "archive", # old model
    "layout_model.pkl": "models",
    
    # Source Code (Moving any existing ones if they match exactly)
    "ads_feature_extraction.py": "src/feature_extraction",
    "project/ads_feature_extraction.py": "src/feature_extraction", # Try this one too
    "competitor_feature_extraction.py": "src/feature_extraction",
    
    "ads_performance_classifier.py": "src/modeling",
    "ads_performance_model.py": "archive", # old file
    "layout_clustering.py": "src/modeling",
    
    "creative_evaluation_engine.py": "src/evaluation",
    "evaluate_new_creative.py": "src/evaluation",
    
    "creative_recommendation_engine.py": "src/integration",
    
    # Reports
    "feature_importance.csv": "reports",
    "performance_plots.png": "reports",
    "cluster_visualizations.png": "reports",
}

# Integration Groups for copying into integration_package
INTEGRATION_GROUPS = {
    "performance_module": [
        "data/company_ads/ads_features.csv",
        "models/creative_performance_model.pkl",
        "data/company_ads/creative_ranked_ads.csv",
        "reports/feature_importance.csv"
    ],
    "layout_module": [
        "data/competitor_ads/competitor_features.csv",
        "data/competitor_ads/layout_clusters.csv",
        "data/competitor_ads/cluster_summary.csv",
        "models/layout_model.pkl"
    ]
}

def create_directory_structure():
    print("STEP 1: Creating directory structure...")
    for dir_path in DIRECTORY_STRUCTURE:
        full_path = os.path.join(TARGET_PROJECT_DIR, dir_path)
        os.makedirs(full_path, exist_ok=True)
        print(f"  Created: {full_path}")
        
    # Also create integration package dirs
    os.makedirs(os.path.join(INTEGRATION_DIR, "performance_module"), exist_ok=True)
    os.makedirs(os.path.join(INTEGRATION_DIR, "layout_module"), exist_ok=True)
    print("  Created: Integration Package Foders")

def move_files():
    print("\nSTEP 2: Moving existing files...")
    for file_name, target_rel_path in FILE_MAPPINGS.items():
        src_file = os.path.join(BASE_DIR, file_name)
        target_dir = os.path.join(TARGET_PROJECT_DIR, target_rel_path)
        target_file = os.path.join(target_dir, os.path.basename(file_name))
        
        if os.path.exists(src_file):
            try:
                # Use shutil.move to move the file
                shutil.move(src_file, target_file)
                print(f"  Moved: {file_name} -> {target_rel_path}/")
            except Exception as e:
                print(f"  [ERROR] Could not move {file_name}: {e}")
        else:
            print(f"  [INFO] File not found (skipping): {file_name}")

def export_integration_package():
    print("\nSTEP 3 & 4: Creating Integration File Groups & Exporting Package...")
    files_prepared = 0
    
    for module_name, files in INTEGRATION_GROUPS.items():
        module_target_dir = os.path.join(INTEGRATION_DIR, module_name)
        print(f"\n  Exporting {module_name}...")
        for rel_path in files:
            src_file = os.path.join(TARGET_PROJECT_DIR, rel_path)
            target_file = os.path.join(module_target_dir, os.path.basename(rel_path))
            
            if os.path.exists(src_file):
                try:
                    shutil.copy2(src_file, target_file)
                    print(f"    Copied: {rel_path}")
                    files_prepared += 1
                except Exception as e:
                    print(f"    [ERROR] Could not copy {rel_path}: {e}")
            else:
                print(f"    [WARNING] Missing file for integration: {rel_path}")
                
    return files_prepared

def print_summary(files_prepared):
    print("\nSTEP 5: Generating Summary...")
    company_ads_count = 0
    competitor_ads_count = 0
    
    company_csv = os.path.join(TARGET_PROJECT_DIR, "data/company_ads/ads_dataset_filtered.csv")
    if os.path.exists(company_csv):
        try:
            df_company = pd.read_csv(company_csv)
            company_ads_count = len(df_company)
        except:
            pass
            
    competitor_csv = os.path.join(TARGET_PROJECT_DIR, "data/competitor_ads/competitor_features.csv")
    if os.path.exists(competitor_csv):
        try:
            df_competitor = pd.read_csv(competitor_csv)
            competitor_ads_count = len(df_competitor)
        except:
            pass

    print("\n" + "="*50)
    print("PROJECT ORGANIZATION SUMMARY")
    print("="*50)
    print(f"Total company ads processed   : {company_ads_count}")
    print(f"Total competitor ads processed: {competitor_ads_count}")
    print(f"Files prepared for integration: {files_prepared}")
    print("="*50)
    print(f"Project repository: {TARGET_PROJECT_DIR}")
    print(f"Integration export: {INTEGRATION_DIR}")

def main():
    print("Starting Project Organization...")
    create_directory_structure()
    move_files()
    files_prepared = export_integration_package()
    print_summary(files_prepared)
    print("Complete!")

if __name__ == "__main__":
    main()
