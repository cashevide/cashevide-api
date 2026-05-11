import json

import requests


class APITest:
    base_url = "http://192.168.31.117/api"
    tokens = {}
    headers = {
        "Content-Type": "application/json",
    }


class Auth(APITest):
    def login(self, email: str, password: str, platform="mobile") -> None:
        url = f"{self.base_url}/users/login/"
        payload = {
            "email": email,
            "password": password,
            "platform": platform,
        }

        try:
            response = requests.post(url, json=payload)

            data = response.json()

            print("\n______________ Login ______________\n")
            print(f"Status Code: {response.status_code}\n")
            print(json.dumps(data, indent=4))

            tokens: dict[str, str | None] = {
                "access": data.get("access"),
                "refresh": data.get("refresh"),
            }

            if response.status_code == 200:
                APITest.tokens = tokens

                if tokens.get("access"):
                    APITest.headers["Authorization"] = f"Bearer {tokens.get('access')}"

        except Exception as e:
            print(f"Error: {e}")

        return None


class Review(APITest):
    def __init__(self) -> None:
        if not APITest.tokens.get("access"):
            print("⚠️ Warning: No access token found! Please login first.")

    def get_clients(self):
        url = f"{self.base_url}/clients/"
        try:
            response = requests.get(url, headers=self.headers)
            data = response.json()

            print("\n______________ Clients ______________\n")
            print(f"Status Code: {response.status_code}\n")
            print(json.dumps(data, indent=4))

        except Exception as e:
            print(f"Error: {e}")

    def post_tags(self):
        url = f"{self.base_url}/tags/"
        payloads = [
            {"name": "On-time Payer", "category": "POSITIVE", "group": "Payment"},
            {"name": "Late Payer", "category": "NEGATIVE", "group": "Payment"},
            {
                "name": "Professional & Respectful",
                "category": "POSITIVE",
                "group": "Behavior",
            },
            {
                "name": "Rude / Unprofessional",
                "category": "NEGATIVE",
                "group": "Behavior",
            },
            {
                "name": "Clear Requirements",
                "category": "POSITIVE",
                "group": "Communication",
            },
            {
                "name": "Ghosting / Unclear",
                "category": "NEGATIVE",
                "group": "Communication",
            },
            {
                "name": "Sticks to Agreement",
                "category": "POSITIVE",
                "group": "Project Scope",
            },
            {
                "name": "Scope Creeper",
                "category": "NEGATIVE",
                "group": "Project Scope",
            },
        ]

        try:
            for payload in payloads:
                response = requests.post(url, json=payload, headers=self.headers)
                data = response.json()
                print(f"Status Code: {response.status_code}\n")
                print(json.dumps(data, indent=4), "\n")

        except Exception as e:
            print(f"Error: {e}")


auth = Auth()
auth.login(email="noufal@email.com", password="noufal")

review = Review()
review.get_clients()
review.post_tags()
