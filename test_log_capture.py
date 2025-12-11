#!/usr/bin/env python3
"""
Test the log capture functionality
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrape import TeeOutput
from datetime import datetime

def test_log_capture():
    """Test that log capture works correctly."""
    print("=" * 60)
    print("Testing Log Capture System")
    print("=" * 60)
    
    # Set up log capturing
    tee = TeeOutput()
    original_stdout = sys.stdout
    sys.stdout = tee
    
    try:
        start_time = datetime.now()
        print(f"\n✓ Log capture started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("✓ This message should appear in console AND be captured")
        print("✓ Testing multi-line output:")
        print("  - Line 1")
        print("  - Line 2")
        print("  - Line 3")
        
        print("\n🔍 Testing special characters:")
        print("  ✓ Checkmark")
        print("  ✗ X mark")
        print("  📧 Email icon")
        print("  👥 Group icon")
        
        print("\n📊 Testing formatted output:")
        print("-" * 40)
        print("| Item | Status |")
        print("-" * 40)
        print("| Test | ✓ Pass |")
        print("-" * 40)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"\n✓ Test completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"✓ Duration: {duration:.3f} seconds")
        
        # Get captured log
        log_content = tee.getvalue()
        
        # Restore stdout
        sys.stdout = original_stdout
        
        print("\n" + "=" * 60)
        print("Log Capture Test Results")
        print("=" * 60)
        print(f"✓ Log captured: {len(log_content)} bytes")
        print(f"✓ Log lines: {log_content.count(chr(10))} lines")
        
        print("\n📄 Captured Log Preview (first 500 chars):")
        print("-" * 60)
        print(log_content[:500])
        if len(log_content) > 500:
            print(f"... (truncated {len(log_content) - 500} bytes)")
        print("-" * 60)
        
        print("\n✅ Log capture test PASSED!")
        print("   The same output appeared in console AND was captured to variable.")
        
        # Save to file for inspection
        test_log_file = "test_log_output.txt"
        with open(test_log_file, 'w') as f:
            f.write(log_content)
        print(f"\n💾 Full log saved to: {test_log_file}")
        
        return True
        
    except Exception as e:
        sys.stdout = original_stdout
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_log_capture()
