try:
    from gui import CrewGUI
    print("GUI imported successfully")
    methods = ["_clean_text", "_read_filter_text", "_save_tts_settings", "_load_tts_settings", "_test_tts"]
    for method in methods:
        if hasattr(CrewGUI, method):
            print(f"Method {method} exists")
        else:
            print(f"Method {method} missing")
except Exception as e:
    print(f"Error: {e}")
