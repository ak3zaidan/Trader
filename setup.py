#!/usr/bin/env python3
"""
Quick setup script for the trading bot
"""

import os
import sys
import shutil
from colorama import Fore, Style, init

init()

def print_banner():
    """Print setup banner"""
    print(f"{Fore.CYAN}")
    print("=" * 50)
    print("    TRADING BOT SETUP")
    print("=" * 50)
    print(f"{Style.RESET_ALL}")

def check_python_version():
    """Check if Python version is compatible"""
    print(f"{Fore.YELLOW}Checking Python version...{Style.RESET_ALL}")
    
    if sys.version_info < (3, 7):
        print(f"{Fore.RED}❌ Python 3.7 or higher is required{Style.RESET_ALL}")
        return False
    
    print(f"{Fore.GREEN}✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible{Style.RESET_ALL}")
    return True

def install_dependencies():
    """Install required dependencies"""
    print(f"{Fore.YELLOW}Installing dependencies...{Style.RESET_ALL}")
    
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirments.txt"])
        print(f"{Fore.GREEN}✅ Dependencies installed successfully{Style.RESET_ALL}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}❌ Failed to install dependencies: {e}{Style.RESET_ALL}")
        return False

def setup_config():
    """Setup configuration file"""
    print(f"{Fore.YELLOW}Setting up configuration...{Style.RESET_ALL}")
    
    if os.path.exists("config.py"):
        print(f"{Fore.YELLOW}config.py already exists. Skipping...{Style.RESET_ALL}")
        return True
    
    if os.path.exists("config_template.py"):
        shutil.copy("config_template.py", "config.py")
        print(f"{Fore.GREEN}✅ Configuration file created from template{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}⚠️  Please edit config.py with your API keys{Style.RESET_ALL}")
        return True
    else:
        print(f"{Fore.RED}❌ config_template.py not found{Style.RESET_ALL}")
        return False

def create_sample_tradable():
    """Create a sample tradable.json for testing"""
    print(f"{Fore.YELLOW}Creating sample tradable tickers...{Style.RESET_ALL}")
    
    if os.path.exists("tradable.json"):
        print(f"{Fore.YELLOW}tradable.json already exists. Skipping...{Style.RESET_ALL}")
        return True
    
    import json
    sample_tickers = [
        "AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", 
        "META", "NVDA", "NFLX", "ADBE", "CRM"
    ]
    
    try:
        with open("tradable.json", "w") as f:
            json.dump(sample_tickers, f, indent=2)
        print(f"{Fore.GREEN}✅ Sample tradable.json created with {len(sample_tickers)} tickers{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"{Fore.RED}❌ Failed to create sample tradable.json: {e}{Style.RESET_ALL}")
        return False

def run_quick_test():
    """Run a quick test to verify setup"""
    print(f"{Fore.YELLOW}Running quick test...{Style.RESET_ALL}")
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, "test.py"], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"{Fore.GREEN}✅ Quick test passed{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}❌ Quick test failed{Style.RESET_ALL}")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"{Fore.YELLOW}⚠️  Test timed out (this is normal if TWS is not running){Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"{Fore.RED}❌ Test failed: {e}{Style.RESET_ALL}")
        return False

def show_next_steps():
    """Show next steps for the user"""
    print(f"\n{Fore.CYAN}=== Setup Complete! ==={Style.RESET_ALL}")
    print(f"{Fore.GREEN}Next steps:{Style.RESET_ALL}")
    print("1. Edit config.py with your API keys")
    print("2. Start IBKR Trader Workstation")
    print("3. Enable API connections in TWS")
    print("4. Run: python start_bot.py")
    print()
    print(f"{Fore.YELLOW}For detailed instructions, see README.md{Style.RESET_ALL}")

def main():
    """Main setup function"""
    print_banner()
    
    steps = [
        ("Python Version Check", check_python_version),
        ("Install Dependencies", install_dependencies),
        ("Setup Configuration", setup_config),
        ("Create Sample Data", create_sample_tradable),
        ("Quick Test", run_quick_test)
    ]
    
    all_passed = True
    
    for step_name, step_func in steps:
        print(f"\n{Fore.CYAN}--- {step_name} ---{Style.RESET_ALL}")
        if not step_func():
            all_passed = False
            print(f"{Fore.RED}❌ {step_name} failed{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}✅ {step_name} completed{Style.RESET_ALL}")
    
    if all_passed:
        show_next_steps()
    else:
        print(f"\n{Fore.RED}❌ Setup failed. Please check the errors above.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
