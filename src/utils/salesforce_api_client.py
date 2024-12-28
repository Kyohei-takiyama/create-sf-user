import json
import logging
from json import JSONDecodeError

import requests
from requests import RequestException
from simple_salesforce import Salesforce  # type: ignore
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from settings import Settings

logger = logging.getLogger(__name__)

# アプリケーション設定を読み込む
settings = Settings()

# デフォルトのタイムアウト値(秒)
DEFAULT_TIMEOUT_SECONDS = 30.0


def init_client() -> Salesforce:
    """
    Salesforce接続用のインスタンスを初期化して返す。
    Settings からユーザー名・パスワード・セキュリティトークンなどを取得。
    """
    return Salesforce(
        username=settings.SF_USER,
        password=settings.SF_PASSWORD,
        security_token=settings.SF_TOKEN,
        domain=settings.SF_DOMAIN,
    )


def parse_json_body(response: requests.Response) -> dict:
    """
    レスポンスのBodyを辞書形式にして返す。
    JSONとしてパースできない場合は、テキストをそのまま返却する。
    """
    try:
        return response.json()
    except JSONDecodeError:
        # JSONとしてパースできなければテキストを返す
        return {
            "message": "response.json() failed",
            "response": response.text
        }


class SalesforceRestApiClient:
    """
    Salesforce REST APIへの共通的なリクエスト機能を提供するクラス。

    初期化時に以下を行う:
      - APIのベースURL + 利用したいpath を合体して self.url に保持。
      - Salesforce接続情報(セッションID等)が含まれる標準ヘッダを作成。
      - 必要であれば additional_headers でカスタムヘッダを上書き/追加。

    公開メソッド:
      - get / post / patch
      - composite_request
      - (内部で send_request を呼び出し、同期で requests リクエストを実行)
    """

    def __init__(
        self,
        path: str,
        additional_headers: dict = None,
    ) -> None:
        """
        :param path: Salesforce REST APIのエンドポイントを表すパス
        :param additional_headers: 任意の追加/上書きヘッダ
        """
        # ベースURL + パス
        self.url = settings.SF_API_BASE_URL + "/" + path.lstrip("/")

        # Salesforceライブラリから取得した標準ヘッダを基に、Content-Typeなど必要ヘッダをセット
        self.base_headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            **init_client().headers,
        }

        # additional_headers があれば上書き
        if additional_headers:
            self.base_headers.update(additional_headers)

    def send_request(
        self,
        method: str,
        headers: dict = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        **kwargs,
    ) -> requests.Response:
        """
        Salesforce REST APIへの共通リクエスト送信処理(同期)。

        :param method: HTTPメソッド (GET, POST, PATCHなど)
        :param headers: 追加/上書きしたいヘッダ
        :param timeout: タイムアウト秒数
        :param kwargs: requests.request() に渡す引数 (params, data, json など)
        :return: requests.Response
        """
        # 最終的に使用するヘッダ(共通ヘッダ + 呼び出し元が渡すヘッダ)
        merged_headers = {**self.base_headers, **(headers or {})}

        # ログ出力用にリクエスト内容をまとめる
        req_info = {
            "method": method,
            "url": self.url,
            "headers": merged_headers,
            "timeout": timeout,
            "kwargs": kwargs,  # params, data など
        }
        logger.info("Salesforce REST API request", extra={"request": req_info})

        response: requests.Response
        try:
            response = requests.request(
                method=method,
                url=self.url,
                headers=merged_headers,
                timeout=timeout,
                **kwargs
            )
            response.raise_for_status()  # エラー時に例外を投げる
            return response

        except RequestException as exc:
            # RequestException: ネットワークエラーなどを包括的に捕捉
            logger.error(
                f"Error occurred for Salesforce REST API request to {self.url}: {exc}"
            )
            # 簡易的にエラーレスポンスとして構築して返却
            error_response = requests.Response()
            error_response.status_code = HTTP_500_INTERNAL_SERVER_ERROR
            return error_response

        except Exception as exc:
            # 予期しないエラー
            logger.error(
                f"Unexpected error occurred for Salesforce REST API request to {self.url}: {exc}"
            )
            error_response = requests.Response()
            error_response.status_code = HTTP_500_INTERNAL_SERVER_ERROR
            return error_response

    def get(self, **kwargs) -> requests.Response:
        """Salesforce REST API への GETリクエスト処理。"""
        return self.send_request("GET", **kwargs)

    def post(self, **kwargs) -> requests.Response:
        """Salesforce REST API への POSTリクエスト処理。"""
        return self.send_request("POST", **kwargs)

    def patch(self, **kwargs) -> requests.Response:
        """Salesforce REST API への PATCHリクエスト処理。"""
        return self.send_request("PATCH", **kwargs)

    def composite_request(self, composite_data: dict) -> requests.Response:
        """
        Salesforce Composite API リクエストを送信するユーティリティ。
        (複数のSalesforce API呼び出しを1リクエストでまとめられる)

        :param composite_data: Composite APIリクエスト用のデータ
        :return: requests.Response
        """
        # リクエストボディをJSON文字列に変換
        request_data = json.dumps(composite_data)
        # バージョンは適宜変更可。例: v52.0 → 最新はv57.0など
        composite_url = f"{settings.SF_API_BASE_URL}/services/data/v52.0/composite"

        # POSTリクエストを実行
        return self.post(
            url=composite_url,
            data=request_data,
            headers={"Content-Length": str(len(request_data))},
        )
