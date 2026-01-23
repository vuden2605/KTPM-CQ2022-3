"""
Test script to verify pipeline setup
Run this before using the full pipeline
"""

import sys
from datetime import datetime

def test_imports():
    """Test if all required packages are installed"""
    print("=" * 60)
    print("Testing imports...")
    print("=" * 60)
    
    try:
        import pandas as pd
        print(f"✓ pandas {pd.__version__}")
    except ImportError as e:
        print(f"✗ pandas not found: {e}")
        return False
    
    try:
        import numpy as np
        print(f"✓ numpy {np.__version__}")
    except ImportError as e:
        print(f"✗ numpy not found: {e}")
        return False
    
    try:
        import pymongo
        print(f"✓ pymongo {pymongo.__version__}")
    except ImportError as e:
        print(f"✗ pymongo not found: {e}")
        return False
    
    try:
        import requests
        print(f"✓ requests {requests.__version__}")
    except ImportError as e:
        print(f"✗ requests not found: {e}")
        return False
    
    print("\n✅ All required packages installed!\n")
    return True


def test_mongodb_connection():
    """Test MongoDB connection"""
    print("=" * 60)
    print("Testing MongoDB connection...")
    print("=" * 60)
    
    try:
        from crypto_data_pipeline import get_mongodb_connection
        
        client = get_mongodb_connection()
        print("✓ MongoDB connection successful")
        
        # List databases
        dbs = client.list_database_names()
        print(f"✓ Found {len(dbs)} databases")
        
        # Check for cryptonews database
        if "cryptonews" in dbs:
            print("✓ 'cryptonews' database exists")
            
            db = client["cryptonews"]
            collections = db.list_collection_names()
            print(f"✓ Found {len(collections)} collections: {collections}")
            
            if "News" in collections:
                news_count = db["News"].count_documents({})
                print(f"✓ News collection has {news_count} documents")
            else:
                print("⚠ 'News' collection not found")
        else:
            print("⚠ 'cryptonews' database not found")
        
        client.close()
        print("\n✅ MongoDB connection test passed!\n")
        return True
        
    except Exception as e:
        print(f"\n✗ MongoDB connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check username/password in crypto_data_pipeline.py")
        print("2. Verify MongoDB cluster URL")
        print("3. Check IP whitelist in MongoDB Atlas")
        print("4. Ensure VPN is not blocking connection\n")
        return False


def test_binance_api():
    """Test Binance API connection"""
    print("=" * 60)
    print("Testing Binance API...")
    print("=" * 60)
    
    try:
        import requests
        
        # Test simple ping
        response = requests.get("https://api.binance.com/api/v3/ping", timeout=5)
        if response.status_code == 200:
            print("✓ Binance API is reachable")
        else:
            print(f"⚠ Binance API returned status {response.status_code}")
            return False
        
        # Test getting server time
        response = requests.get("https://api.binance.com/api/v3/time", timeout=5)
        if response.status_code == 200:
            server_time = response.json()['serverTime']
            print(f"✓ Binance server time: {datetime.fromtimestamp(server_time/1000)}")
        
        # Test getting BTCUSDT price
        response = requests.get(
            "https://api.binance.com/api/v3/ticker/price",
            params={"symbol": "BTCUSDT"},
            timeout=5
        )
        if response.status_code == 200:
            price = response.json()['price']
            print(f"✓ BTCUSDT price: ${float(price):,.2f}")
        
        print("\n✅ Binance API test passed!\n")
        return True
        
    except Exception as e:
        print(f"\n✗ Binance API test failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check internet connection")
        print("2. Verify firewall/proxy settings")
        print("3. Try accessing https://www.binance.com in browser\n")
        return False


def test_small_pipeline():
    """Test pipeline with small dataset"""
    print("=" * 60)
    print("Testing pipeline with small dataset...")
    print("=" * 60)
    
    try:
        from crypto_data_pipeline import run_pipeline
        
        # Run with just 2 days of data
        df = run_pipeline(
            symbol="BTCUSDT",
            interval="1h",
            start_date="2026-01-20",
            end_date="2026-01-22",
            save_to_mongodb=False,
            save_to_csv=False
        )
        
        if df is not None and not df.empty:
            print(f"\n✅ Pipeline test passed!")
            print(f"   Generated {len(df)} samples")
            print(f"   Features: {len(df.columns)}")
            print(f"   Date range: {df.index.min()} to {df.index.max()}")
            return True
        else:
            print("\n⚠ Pipeline returned empty dataset")
            return False
        
    except Exception as e:
        print(f"\n✗ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("CRYPTO DATA PIPELINE - SYSTEM TEST")
    print("=" * 60 + "\n")
    
    results = {
        "Imports": test_imports(),
        "Binance API": test_binance_api(),
        "MongoDB": test_mongodb_connection(),
        "Small Pipeline": test_small_pipeline()
    }
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! System is ready.")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Update MongoDB credentials in crypto_data_pipeline.py")
        print("2. Run the full pipeline with your desired date range")
        print("3. Check output files and MongoDB collection")
    else:
        print("⚠️  SOME TESTS FAILED. Please fix issues above.")
        print("=" * 60)
        print("\nCommon issues:")
        print("- Missing packages: run 'pip install -r requirements.txt'")
        print("- MongoDB credentials: update in crypto_data_pipeline.py")
        print("- Network issues: check firewall/VPN")
    print()
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
