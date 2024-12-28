import os
import sys
from settings import Settings

from functions.create_users import create_users_from_csv

def main():
    settings = Settings()
    env_name = settings.Config.env

    print(f"実行環境: {env_name}")

    # もし本番実行の場合に確認プロンプトを出す
    if env_name == "prod":
        confirm = input("⚠️ 本番環境で実行します。よろしいですか？ (yes/no): ")
        if confirm.lower() not in ("yes", "y"):
            print("====== 処理中断 ====== ")
            sys.exit(1)

    # ここから処理を実行
    print("====== 処理開始 ======")

    create_users_from_csv("src/files/ユーザー作成シート.csv")
if __name__ == "__main__":
    main()