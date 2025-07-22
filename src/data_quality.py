import pandas as pd

def check_non_nulls(df: pd.DataFrame) -> dict:
    non_null_counts = df.notnull().sum()
    total_non_nulls = non_null_counts.sum()
    return {
        "total_non_nulls": int(total_non_nulls),
        "non_nulls_by_column": non_null_counts.to_dict()
    }

def check_nulls(df: pd.DataFrame) -> dict:
    null_counts = df.isnull().sum()
    total_nulls = null_counts.sum()
    return {
        "total_nulls": int(total_nulls),
        "nulls_by_column": null_counts.to_dict()
    }

def check_duplicates(df: pd.DataFrame) -> dict:
    duplicate_count = df.duplicated().sum()
    return {"duplicate_rows": int(duplicate_count)}

def check_empty_strings(df: pd.DataFrame) -> dict:
    empty_counts = {
        col: (df[col].astype(str).str.strip() == '').sum()
        for col in df.columns if df[col].dtype == object
    }
    total_empty = sum(empty_counts.values())
    return {
        "total_empty_strings": int(total_empty),
        "empty_strings_by_column": empty_counts
    }

def run_data_quality_checks(df: pd.DataFrame) -> dict:
    results = {}
    results.update(check_non_nulls(df))
    results.update(check_nulls(df))
    results.update(check_duplicates(df))
    results.update(check_empty_strings(df))
    return results
