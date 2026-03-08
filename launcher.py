"""
BMW M4 Dual Display System Launcher
Deschide simulatorul Redline_Revving_Sim și ecranul Sport (ecran_sport) simultan
Cu opțiuni customize pentru dimensiuni ferestre
"""

import subprocess
import sys
import os
import time
import json

def load_config(current_dir):
    """Încarcă configurația din fișierul config.json"""
    config_path = os.path.join(current_dir, "config.json")
    default_config = {
        "redline_width": 1100,
        "redline_height": 600,
        "sport_width": 1000,
        "sport_height": 700
    }
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except:
            return default_config
    return default_config

def save_config(current_dir, config):
    """Salvează configurația în fișierul config.json"""
    config_path = os.path.join(current_dir, "config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config = load_config(current_dir)
    
    print("\n" + "=" * 70)
    print("🏎️  BMW M4 DUAL DISPLAY SYSTEM - LAUNCHER")
    print("=" * 70)
    print("\n📏 DIMENSIUNI RECOMANDATE:\n")
    print("  [ENTER] → Standard (1100x600 & 1000x700) ⭐ RECOMANDAT")
    print("  [L]     → Large (1280x720 & 1200x800)")
    print("  [S]     → Small (1024x600 & 800x550)")
    print("  [F]     → Full HD (1920x1080 & 1600x1000)")
    print("  [C]     → Custom")
    
    choice = input("\n👉 Alege [(ENTER)/L/S/F/C]: ").strip().upper()
    
    if choice == "" or choice == "ENTER":
        config["redline_width"] = 1100
        config["redline_height"] = 600
        config["sport_width"] = 1000
        config["sport_height"] = 700
        print("✓ Standard sizing selected")
    elif choice == "L":
        config["redline_width"] = 1280
        config["redline_height"] = 720
        config["sport_width"] = 1200
        config["sport_height"] = 800
        print("✓ Large sizing selected")
    elif choice == "S":
        config["redline_width"] = 1024
        config["redline_height"] = 600
        config["sport_width"] = 800
        config["sport_height"] = 550
        print("✓ Small sizing selected")
    elif choice == "F":
        config["redline_width"] = 1920
        config["redline_height"] = 1080
        config["sport_width"] = 1600
        config["sport_height"] = 1000
        print("✓ Full HD sizing selected")
    elif choice == "C":
        print("\n⚙️  DIMENSIUNI CUSTOMIZATE:\n")
        try:
            redline_w = int(input("  Lățime Redline (default 1100): ") or 1100)
            redline_h = int(input("  Înălțime Redline (default 600): ") or 600)
            sport_w = int(input("  Lățime Sport Display (default 1000): ") or 1000)
            sport_h = int(input("  Înălțime Sport Display (default 700): ") or 700)
            
            config["redline_width"] = redline_w
            config["redline_height"] = redline_h
            config["sport_width"] = sport_w
            config["sport_height"] = sport_h
            print("✓ Custom sizing saved")
        except ValueError:
            print("❌ Input invalid! Se folosesc dimensiunile standard.")
            config["redline_width"] = 1100
            config["redline_height"] = 600
            config["sport_width"] = 1000
            config["sport_height"] = 700
    else:
        print("❌ Opțiune invalidă! Se folosesc dimensiunile standard.")
        config["redline_width"] = 1100
        config["redline_height"] = 600
        config["sport_width"] = 1000
        config["sport_height"] = 700
    
    # Salvează configurația
    save_config(current_dir, config)
    
    # Căi către scripturile de rulare
    redline_script = os.path.join(current_dir, "Redline_Revving_Sim.py")
    sport_script = os.path.join(current_dir, "ecran_sport.py")
    
    # Verifică dacă fișierele există
    if not os.path.exists(redline_script):
        print(f"\n❌ Eroare: Redline_Revving_Sim.py nu a fost găsit!")
        print(f"  Path: {redline_script}")
        input("Press ENTER to exit...")
        return
    
    if not os.path.exists(sport_script):
        print(f"❌ Eroare: ecran_sport.py nu a fost găsit!")
        print(f"  Path: {sport_script}")
        input("Press ENTER to exit...")
        return
    
    try:
        print("\n" + "=" * 70)
        print("🚀 Se lansează simulatoarele...\n")
        
        print(f"📊 Dashboard (Redline): {config['redline_width']}x{config['redline_height']}")
        process1 = subprocess.Popen([sys.executable, redline_script], cwd=current_dir)
        
        time.sleep(2)
        
        print(f"🎨 iDrive Display (Sport): {config['sport_width']}x{config['sport_height']}")
        process2 = subprocess.Popen([sys.executable, sport_script], cwd=current_dir)
        
        print("\n" + "=" * 70)
        print("✅ AMBELE PROGRAME SUNT ACTIVE!")
        print("=" * 70)
        print("\n🎮 COMENZI:")
        print("  SPACE  → Turează motorul în Neutral (N)")
        print("  ENTER  → Accelerează în Drive (D)")
        print("  SHIFT  → Frână Carbon")
        print("\n💡 Pentru a închide: Apasă X pe oricare din ferestre")
        print("=" * 70 + "\n")
        
        # Așteptă ca procesele să se termine
        process1.wait()
        process2.wait()
        
    except Exception as e:
        print(f"❌ Eroare la lansare: {e}")
        import traceback
        traceback.print_exc()
        input("Press ENTER to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()

