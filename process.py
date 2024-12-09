import os
import json
import pandas as pd


# Step 1: Remove empty JSON files
def delete_empty_json_files(folder_path):
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".json"):
            file_path = os.path.join(folder_path, file_name)
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                if not data:  # Check if data is empty
                    os.remove(file_path)
            except Exception:
                pass


# Step 2: Convert JSON to CSV
def convert_json_to_csv(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    for file_name in os.listdir(input_folder):
        if file_name.endswith(".json"):
            input_file_path = os.path.join(input_folder, file_name)
            output_file_name = file_name.replace(".json", ".csv")
            output_file_path = os.path.join(output_folder, output_file_name)
            try:
                with open(input_file_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                if isinstance(data, list) and data:
                    df = pd.DataFrame(data)
                    df.to_csv(output_file_path, index=False, encoding="utf-8-sig")
            except Exception:
                pass


# Step 3: Add percentage column
def add_percentage_column(folder_path):
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".csv"):
            file_path = os.path.join(folder_path, file_name)
            df = pd.read_csv(file_path)
            if {'totnmrs', 'prfdtcnt', 'seatcnt'}.issubset(df.columns):
                df['percentage'] = ((df['totnmrs'] / (df['prfdtcnt'] * df['seatcnt'])) * 100).round(2)
                df.to_csv(file_path, index=False)


# Step 4: Remove rows with null percentage
def remove_null_percentage_rows(folder_path):
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".csv"):
            file_path = os.path.join(folder_path, file_name)
            df = pd.read_csv(file_path)
            if 'percentage' in df.columns:
                df = df.dropna(subset=['percentage'])
                df.to_csv(file_path, index=False)


# Step 5: Combine title, prfnmfct, and prfnmplc columns
def combine_columns(folder_path):
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".csv"):
            file_path = os.path.join(folder_path, file_name)
            df = pd.read_csv(file_path)
            if {'title', 'prfnmfct', 'prfnmplc', 'percentage'}.issubset(df.columns):
                df['combined'] = df['title'] + "_" + df['prfnmfct'] + " (" + df['prfnmplc'] + ")"
                df = df[['combined', 'percentage']]
                df.to_csv(file_path, index=False)


# Step 6: Merge all CSV files
def merge_csv_files(folder_path, output_file):
    dataframes = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".csv"):
            file_path = os.path.join(folder_path, file_name)
            df = pd.read_csv(file_path)
            dataframes.append(df)
    if dataframes:
        merged_df = pd.concat(dataframes, ignore_index=True)
        merged_df.to_csv(output_file, index=False)


# Step 7: Convert musical_details.json to CSV with 'combined' column
def convert_musical_details(input_file, output_file):
    try:
        with open(input_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, list):
            df = pd.DataFrame(data)
            if {'title', 'place'}.issubset(df.columns):
                df['combined'] = df['title'] + "_" + df['place']
            df.to_csv(output_file, index=False, encoding="utf-8-sig")
    except Exception:
        pass


# Step 8: Merge merged CSV with musical_details.csv
def merge_with_details(file1, file2, output_file):
    try:
        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)
        if 'combined' in df1.columns and 'combined' in df2.columns:
            merged_df = pd.merge(df1, df2, on='combined', how='inner')
            merged_df.to_csv(output_file, index=False)
    except Exception:
        pass


# Step 9: Remove combined column
def remove_combined_column(file_path):
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        if 'combined' in df.columns:
            df = df.drop(columns=['combined'])
            df.to_csv(file_path, index=False)


# Step 10: Convert final CSV to JSON
def convert_csv_to_json(input_file, output_file):
    df = pd.read_csv(input_file)
    df.to_json(output_file, orient='records', lines=False, force_ascii=False, indent=4)


# Final Step: Clean and Rename Title Columns in JSON, Remove Unnecessary Columns
def clean_and_rename_title(input_file, output_file):
    try:
        # Load the JSON file as a DataFrame
        df = pd.read_json(input_file, orient='records')

        # Drop unnecessary columns if they exist
        columns_to_remove = ['title_x', 'errmsg', 'responsetime', 'returncode']
        for col in columns_to_remove:
            if col in df.columns:
                df = df.drop(columns=[col])

        # Rename 'title_y' to 'title' if it exists
        if 'title_y' in df.columns:
            df = df.rename(columns={'title_y': 'title'})

        # Save the modified DataFrame back to JSON
        df.to_json(output_file, orient='records', lines=False, force_ascii=False, indent=4)
        print(f"Updated JSON saved to {output_file}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    # Define file paths and directories
    json_folder = "results"
    csv_folder = "csv_results"
    merged_csv = "merged_file.csv"
    musical_details_json = "musical_details.json"
    musical_details_csv = "musical_details.csv"
    final_csv = "merged_result.csv"
    final_json = "percentage_raw.json"
    cleaned_json = "per+raw.json"

    # Execute steps in sequence
    delete_empty_json_files(json_folder)
    convert_json_to_csv(json_folder, csv_folder)
    add_percentage_column(csv_folder)
    remove_null_percentage_rows(csv_folder)
    combine_columns(csv_folder)
    merge_csv_files(csv_folder, merged_csv)
    convert_musical_details(musical_details_json, musical_details_csv)
    merge_with_details(merged_csv, musical_details_csv, final_csv)
    remove_combined_column(final_csv)
    convert_csv_to_json(final_csv, final_json)

    # Final step: Clean and rename title in JSON, and remove unnecessary columns
    clean_and_rename_title(final_json, cleaned_json)
