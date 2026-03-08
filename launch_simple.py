#!/usr/bin/env python3
"""
Simple Direct Launcher - Bypasses PATH issues
"""

import subprocess
import sys
import os
import time
import json

def set_window_sizes():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "config.json")
    
    print("\n" + "="*70)
    print("🏎️  BMW M4 DUAL DISPLAY SYSTEM")
    print("="*70)
    print("\n📏 RECOMMENDED SIZES:\n")
    print("  1 = Standard (1100x600 & 1000x700) ⭐")
    print("  2 = Large (1280x720 & 1200x800)")
    print("  3 = Small (1024x600 & 800x550)")
    print("  4 = Full HD (1920x1080 & 1600x1000)")
    
    choice = input("\nChoose [1-4] (press ENTER for Standard): ").strip()
    
    sizes = {
        "1": (1100, 600, 1000, 700),
        "2": (1280, 720, 1200, 800),
        "3": (1024, 600, 800, 550),
        "4": (1920, 1080, 1600, 1000),
        "": (1100, 600, 1000, 700),  # Default
    }
    
    if choice not in sizes:
        choice = "1"
    
    redline_w, redline_h, sport_w, sport_h = sizes[choice]
    
    config = {
        "redline_width": redline_w,
        "redline_height": redline_h,
        "sport_width": sport_w,
        "sport_height": sport_h
    }
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    
    return redline_w, redline_h, sport_w, sport_h

def main():
    try:
        print("\n⏳ Configuring window sizes...")
        redline_w, redline_h, sport_w, sport_h = set_window_sizes()
        print(f"✓ Redline: {redline_w}x{redline_h}")
        print(f"✓ Sport:   {sport_w}x{sport_h}")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        print("\n🚀 Launching applications...\n")
        
        # Launch Redline_Revving_Sim.py
        redline_path = os.path.join(current_dir, "Redline_Revving_Sim.py")
        if not os.path.exists(redline_path):
            print(f"❌ ERROR: Redline_Revving_Sim.py not found!")
            return False
        
        print("📊 Starting Dashboard (Redline_Revving_Sim)...")
        p1 = subprocess.Popen([sys.executable, redline_path], cwd=current_dir)
        time.sleep(2)
        
        # Launch ecran_sport.py
        sport_path = os.path.join(current_dir, "ecran_sport.py")
        if not os.path.exists(sport_path):
            print(f"❌ ERROR: ecran_sport.py not found!")
            return False
        
        print("🎨 Starting Sport Display (ecran_sport)...")
        p2 = subprocess.Popen([sys.executable, sport_path], cwd=current_dir)
        
        print("\n" + "="*70)
        print("✅ BOTH SIMULATORS ARE RUNNING!")
        print("="*70)
        print("\n🎮 CONTROLS:")
        print("  SPACE  → Rev engine in Neutral (N)")
        print("  ENTER  → Accelerate in Drive (D)")
        print("  SHIFT  → Brake")
        print("\n  Close either window to stop the simulator")
        print("="*70 + "\n")
        
        # Wait for both to finish
        p1.wait()
        p2.wait()
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        input("\nPress ENTER to exit...")
        sys.exit(1)
