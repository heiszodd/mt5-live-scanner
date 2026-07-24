import argparse
import os
import mt5

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--login", type=int, help="Login ID")
    parser.add_argument("--password", type=str, help="Password")
    parser.add_argument("--server", type=str, help="Server")
    args = parser.parse_args()

    # Fallback to environment variables if args not provided
    login = args.login or (int(os.getenv("MT5_LOGIN")) if os.getenv("MT5_LOGIN") else None)
    password = args.password or os.getenv("MT5_PASSWORD")
    server = args.server or os.getenv("MT5_SERVER")

    init_kwargs = {}
    if login and password and server:
        init_kwargs = {"login": login, "password": password, "server": server}
    mt5.initialize(**init_kwargs)

    print("MT5 version:", mt5.version())
    info = mt5.account_info()
    if info:
        print("Account:", getattr(info, "name", "N/A"))
        print("Leverage:", getattr(info, "leverage", "N/A"))
        print("Equity:", getattr(info, "equity", "N/A"))
        print("Balance:", getattr(info, "balance", "N/A"))
        print("Server:", getattr(info, "server", "N/A"))
    else:
        print("Failed to retrieve account information")

    mt5.shutdown()

if __name__ == "__main__":
    main()
