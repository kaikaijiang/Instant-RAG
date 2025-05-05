import yaml
import os
import sys

def test_config_loading():
    """Test loading the configuration from config.yaml"""
    try:
        # Load the config file
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        
        # Check if system_prompt is in the config
        if 'system_prompt' in config:
            print("✅ system_prompt found in config.yaml")
            # Print the first 50 characters of the system_prompt
            print(f"Preview: {config['system_prompt'][:50]}...")
        else:
            print("❌ system_prompt not found in config.yaml")
        
        # Check if LLM parameters are in the config
        if 'llm' in config:
            print("\n✅ LLM parameters found in config.yaml:")
            for key, value in config['llm'].items():
                print(f"  - {key}: {value}")
        else:
            print("\n❌ LLM parameters not found in config.yaml")
            
        # Check if Chat parameters are in the config
        if 'chat' in config:
            print("\n✅ Chat parameters found in config.yaml:")
            for key, value in config['chat'].items():
                print(f"  - {key}: {value}")
        else:
            print("\n❌ Chat parameters not found in config.yaml")
        
        return True
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False

if __name__ == "__main__":
    print("Testing config.yaml loading...")
    success = test_config_loading()
    if success:
        print("\nNow testing run.py config loading...")
        # Import the run module to test its config loading
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        import run
        
        # Load the config using run.py's function
        run.load_config('config.yaml')
        
        # Check if the config was loaded correctly
        if run.config and 'system_prompt' in run.config:
            print("✅ run.py successfully loaded system_prompt from config.yaml")
            print(f"Preview: {run.config['system_prompt'][:50]}...")
        else:
            print("❌ run.py failed to load system_prompt from config.yaml")
        
        # Check if LLM parameters were loaded correctly
        if run.config and 'llm' in run.config:
            print("\n✅ run.py successfully loaded LLM parameters from config.yaml:")
            for key, value in run.config['llm'].items():
                print(f"  - {key}: {value}")
        else:
            print("\n❌ run.py failed to load LLM parameters from config.yaml")
            
        # Check if Chat parameters were loaded correctly
        if run.config and 'chat' in run.config:
            print("\n✅ run.py successfully loaded Chat parameters from config.yaml:")
            for key, value in run.config['chat'].items():
                print(f"  - {key}: {value}")
        else:
            print("\n❌ run.py failed to load Chat parameters from config.yaml")
    
    print("\nTest completed.")
