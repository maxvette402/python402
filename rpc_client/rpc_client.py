import requests
import json
import base64
from typing import Optional, Any, Dict

# Configuration Constants
ENDPOINT = "http://127.0.0.1:8332"
USER = "bitcoin-rpc-user"
PASSWORD = "bitcoin-rpc-password"
TIMEOUT = 30


class JsonRPCClient:
    """Bitcoin Core JSON-RPC Client"""

    def __init__(self, url: str = ENDPOINT, user: str = USER, password: str = PASSWORD, timeout: int = TIMEOUT):
        self.url = url
        self.timeout = timeout

        # Prepare Basic Auth header
        credentials = f"{user}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {encoded_credentials}'
        }

        self._id = 0

    def request(self, method: str, params: Optional[list] = None) -> Any:
        """
        Make a JSON-RPC request to Bitcoin Core

        Args:
            method: RPC method name (e.g., 'getblockchaininfo')
            params: List of parameters for the RPC method

        Returns:
            The result from the RPC call

        Raises:
            Exception: On any error with user-friendly message and technical details
        """
        if params is None:
            params = []

        self._id += 1

        payload = {
            "jsonrpc": "2.0",
            "id": self._id,
            "method": method,
            "params": params
        }

        try:
            response = requests.post(
                self.url,
                data=json.dumps(payload),
                headers=self.headers,
                timeout=self.timeout
            )

            # Handle HTTP errors
            if response.status_code == 401:
                raise Exception(
                    "Authentication failed. Please check your RPC username and password.\n"
                    f"Technical details: HTTP 401 - Unauthorized. "
                    f"Endpoint: {self.url}, User: {USER}"
                )
            elif response.status_code == 403:
                raise Exception(
                    "Access forbidden. Your RPC user may not have permission for this operation.\n"
                    f"Technical details: HTTP 403 - Forbidden. Method: {method}"
                )
            elif response.status_code != 200:
                raise Exception(
                    f"Bitcoin node returned an error (HTTP {response.status_code}).\n"
                    f"Technical details: {response.text}"
                )

            # Parse JSON response
            try:
                rpc_response = response.json()
            except json.JSONDecodeError as e:
                raise Exception(
                    "Bitcoin node returned invalid JSON response.\n"
                    f"Technical details: JSON decode error: {str(e)}\n"
                    f"Raw response: {response.text[:500]}..."
                )

            # Handle JSON-RPC errors
            if 'error' in rpc_response and rpc_response['error'] is not None:
                error = rpc_response['error']
                error_code = error.get('code', 'Unknown')
                error_message = error.get('message', 'Unknown error')

                raise Exception(
                    f"Bitcoin RPC error: {error_message}\n"
                    f"Technical details: Error code {error_code}, Method: {method}, "
                    f"Params: {params}"
                )

            # Return the result
            return rpc_response.get('result')

        except requests.exceptions.ConnectionError as e:
            raise Exception(
                "Could not connect to Bitcoin node. Is Bitcoin Core running?\n"
                f"Technical details: Connection error to {self.url}: {str(e)}"
            )
        except requests.exceptions.Timeout as e:
            raise Exception(
                f"Bitcoin node did not respond within {self.timeout} seconds.\n"
                f"Technical details: Timeout error: {str(e)}"
            )
        except requests.exceptions.RequestException as e:
            raise Exception(
                "Network error while connecting to Bitcoin node.\n"
                f"Technical details: Request exception: {str(e)}"
            )

    def getblockchaininfo(self) -> Dict[str, Any]:
        """Get blockchain information"""
        return self.request("getblockchaininfo")

    def getbestblockhash(self) -> str:
        """Get the hash of the best block"""
        return self.request("getbestblockhash")

    def getblockcount(self) -> int:
        """Get the current block height"""
        return self.request("getblockcount")

    def getnetworkinfo(self) -> Dict[str, Any]:
        """Get network information"""
        return self.request("getnetworkinfo")


def main():
    """Main function - called when script is run directly"""
    print("Connecting to Bitcoin Core RPC...")
    print(f"Endpoint: {ENDPOINT}")
    print(f"User: {USER}")
    print("=" * 50)

    try:
        client = JsonRPCClient()
        result = client.getblockchaininfo()

        print("SUCCESS! Bitcoin Core blockchain info:")
        print(json.dumps(result, indent=2, sort_keys=True))

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())