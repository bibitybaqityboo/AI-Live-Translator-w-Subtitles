import os
import subprocess
import shutil
import customtkinter

def build():
    # Get the path to customtkinter to include its assets
    ctk_path = os.path.dirname(customtkinter.__file__)
    # Add-data format for Windows is "source;dest"
    add_data_ctk = f"{ctk_path};customtkinter/"

    apps_to_build = [
        {
            "name": "Live Voice Translator",
            "script": "Live Voice Translator/live_translate_gui.py",
            "output_name": "AI_Live_Translate"
        },
        {
            "name": "Game Audio Translator",
            "script": "Game Audio Translator/game_translate_gui.py",
            "output_name": "AI_Game_Audio_Translator"
        },
        {
            "name": "Gaming Subtitles",
            "script": "Gaming Subtitles/subtitle_overlay.py",
            "output_name": "AI_Gaming_Subtitles"
        }
    ]

    base_dir = os.path.dirname(os.path.abspath(__file__))
    releases_dir = os.path.join(base_dir, "Releases")
    if not os.path.exists(releases_dir):
        os.makedirs(releases_dir)

    for app in apps_to_build:
        print(f"\\n[{app['name']}] Starting build process...")
        script_path = os.path.join(base_dir, app["script"])
        
        command = [
            "python", "-m", "PyInstaller",
            "--noconfirm",
            "--onefile",
            "--windowed", # Do not show console window
            "--name", app["output_name"],
            "--add-data", add_data_ctk,
            "--hidden-import", "pyaudio",
            "--hidden-import", "google.genai",
            "--hidden-import", "pygame",
            script_path
        ]
        
        print(f"Running command: {' '.join(command)}")
        subprocess.run(command, check=True)
        
        # Move the resulting executable to the Releases folder
        exe_path = os.path.join(base_dir, "dist", f"{app['output_name']}.exe")
        dest_path = os.path.join(releases_dir, f"{app['output_name']}.exe")
        
        if os.path.exists(exe_path):
            shutil.move(exe_path, dest_path)
            print(f"[{app['name']}] Successfully built and moved to Releases!")
        else:
            print(f"[{app['name']}] Failed to build (executable not found in dist).")

    # Clean up PyInstaller build artifacts
    print("\\nCleaning up build artifacts...")
    for folder in ["build", "dist"]:
        path = os.path.join(base_dir, folder)
        if os.path.exists(path):
            shutil.rmtree(path)
            
    for spec in os.listdir(base_dir):
        if spec.endswith(".spec"):
            os.remove(os.path.join(base_dir, spec))

    print("\\nAll builds finished! Executables are located in the Releases folder.")

if __name__ == "__main__":
    build()
