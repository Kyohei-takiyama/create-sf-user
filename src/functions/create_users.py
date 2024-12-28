import csv
import json

from utils.salesforce_api_client import SalesforceRestApiClient

"""
前提:
- CSVなどからユーザ候補データを読み込んで作成する例
- CSV: users.csv (カラム例)
  FirstName,LastName,Email,Username,Alias,TimeZoneSidKey,LocaleSidKey,EmailEncodingKey,LanguageLocaleKey,ProfileId
"""

def create_users_from_csv(csv_file_path):
    # Salesforce APIクライアントを初期化
    sf = SalesforceRestApiClient(path="/services/data/v50.0/sobjects/User")

    with open(csv_file_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                user_record = {
                    "FirstName": row["FirstName"],
                    "LastName": row["LastName"],
                    "Email": row["Email"],
                    "Username": row["Username"],
                    "Alias": row["Alias"],
                    "TimeZoneSidKey": row["TimeZoneSidKey"],
                    "LocaleSidKey": row["LocaleSidKey"],
                    "EmailEncodingKey": row["EmailEncodingKey"],
                    "LanguageLocaleKey": row["LanguageLocaleKey"],
                    "ProfileId": row["ProfileId"]
                }
                # ユーザ作成実行
                result = sf.post(data=json.dumps(user_record))
                print(f"Successfully created user: {row['Username']} -> {result}")
            except Exception as e:
                print(f"Failed to create user: {row.get('Username', 'No Username')} -> {str(e)}")