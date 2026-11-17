import os
import glob
import json
import pandas as pd
import openpyxl

def audit_who():
    who_path = os.path.join("data", "raw", "who_diabetes", "data.csv")
    if not os.path.exists(who_path):
        print(f"ERROR: {who_path} not found")
        return None
    
    size_bytes = os.path.getsize(who_path)
    df = pd.read_csv(who_path)
    
    indicators = df["IndicatorCode"].unique().tolist()
    sex_codes = df["Dim1ValueCode"].unique().tolist()
    age_codes = df["Dim2ValueCode"].unique().tolist()
    
    # Filter
    filtered = df[
        (df["IndicatorCode"] == "NCD_DIABETES_PREVALENCE_AGESTD") &
        (df["Dim1ValueCode"] == "SEX_BTSX") &
        (df["Dim2ValueCode"] == "AGEGROUP_YEARS18-PLUS")
    ].copy()
    
    loc_counts = filtered["Location"].value_counts()
    
    # Checks
    bounds_ok = (
        (filtered["FactValueNumericLow"] <= filtered["FactValueNumeric"]) &
        (filtered["FactValueNumeric"] <= filtered["FactValueNumericHigh"])
    ).all()
    
    range_ok = (
        (filtered["FactValueNumeric"] >= 0) &
        (filtered["FactValueNumeric"] <= 100)
    ).all()
    
    dups = filtered.duplicated(subset=["Location", "Period"]).sum()
    nulls = filtered[["Location", "Period", "FactValueNumeric", "FactValueNumericLow", "FactValueNumericHigh"]].isnull().sum().to_dict()
    
    res = {
        "path": who_path,
        "size_bytes": size_bytes,
        "raw_shape": list(df.shape),
        "columns": list(df.columns),
        "indicators": indicators,
        "sex_codes": sex_codes,
        "age_codes": age_codes,
        "filtered_shape": list(filtered.shape),
        "unique_locations": int(filtered["Location"].nunique()),
        "year_min": int(filtered["Period"].min()),
        "year_max": int(filtered["Period"].max()),
        "locations_33_years": int((loc_counts == 33).sum()),
        "locations_other_years": {k: int(v) for k, v in loc_counts[loc_counts != 33].items()},
        "bounds_valid": bool(bounds_ok),
        "range_valid_0_100": bool(range_ok),
        "duplicate_location_years": int(dups),
        "null_counts": nulls,
        "prevalence_min": float(filtered["FactValueNumeric"].min()),
        "prevalence_max": float(filtered["FactValueNumeric"].max()),
        "prevalence_mean": float(filtered["FactValueNumeric"].mean()),
        "prevalence_median": float(filtered["FactValueNumeric"].median()),
        "prevalence_std": float(filtered["FactValueNumeric"].std())
    }
    return res

def audit_gbd():
    results = {}
    gbd_files = sorted(glob.glob("data/raw/gbd2023/*.XLSX"))
    for f in gbd_files:
        basename = os.path.basename(f)
        wb = openpyxl.load_workbook(f, read_only=True)
        sheets = wb.sheetnames
        
        # Read first sheet
        df = pd.read_excel(f, sheet_name=sheets[0])
        
        # Look for diabetes
        matches = []
        for col in df.columns:
            if any(k in str(col).lower() for k in ["cause", "name", "disease", "condition", "risk", "measure"]):
                m = df[df[col].astype(str).str.contains("diabetes", case=False, na=False)][col].unique().tolist()
                if m:
                    matches.extend(m)
        
        results[basename] = {
            "size_bytes": os.path.getsize(f),
            "sheets": sheets,
            "shape": list(df.shape),
            "columns": [str(c) for c in df.columns[:25]],
            "has_diabetes": len(matches) > 0,
            "diabetes_matches": list(set(matches))[:5]
        }
    return results

def audit_papers():
    results = {}
    papers = sorted(glob.glob("data/raw/research_papers/*.pdf"))
    for p in papers:
        results[os.path.basename(p)] = {
            "size_bytes": os.path.getsize(p)
        }
    return results

if __name__ == "__main__":
    who_res = audit_who()
    gbd_res = audit_gbd()
    papers_res = audit_papers()
    
    full_audit = {
        "who": who_res,
        "gbd": gbd_res,
        "papers": papers_res
    }
    
    os.makedirs("reports", exist_ok=True)
    with open("reports/inventory_audit_raw.json", "w") as out:
        json.dump(full_audit, out, indent=2)
        
    print("SUCCESS: Inventory audit completed.")
    print(f"WHO raw shape: {who_res['raw_shape']}, filtered: {who_res['filtered_shape']}")
    print(f"GBD files audited: {len(gbd_res)}")
    print(f"Research papers found: {len(papers_res)}")

