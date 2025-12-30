import os
import sys
from google import genai
from agent_tools.genai_client import client

from agent_tools import (
    list_base_renders,
    run_nano_variant,
    log_result,
)

# --------------------------------------------------
# Environment / client setup
# --------------------------------------------------

MODEL_NAME = "gemini-3-pro-preview"


# --------------------------------------------------
# System prompt loader (optional, kept for reference)
# --------------------------------------------------

def load_system_prompt() -> str:
    """
    Load the system prompt from agent_prompt.txt.
    This is not strictly required by the current image pipeline,
    but is kept for compatibility / future expansion.
    """
    prompt_path = "agent_prompt.txt"
    if not os.path.exists(prompt_path):
        print(f"WARNING: {prompt_path} not found. Using a default prompt.")
        return (
            "You are an architectural visualization assistant. "
            "Your job is to take base D5 renders and generate lighting variants "
            "such as morning, noon, sunset, and night. "
            "Preserve building geometry and camera angle. "
            "Keep all edits realistic and professional."
        )
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


# --------------------------------------------------
# Batch processing using your current tools
# --------------------------------------------------

def process_agent_task(system_prompt: str):
    """
    Batch process all base renders in /input using the current
    run_nano_variant function (Gemini 3 Pro + Image).
    """
    print("\n" + "=" * 60)
    print("Starting AI Agent for D5 Render Lighting Variants")
    print("Using Gemini 3 Pro + Image (current setup)")
    print("=" * 60 + "\n")

    # Style preset and resolution for this run
    # Must match a key in styles.json
    style_name = "pelli_modern"
    resolution = "4K"  # or "1K" / "2K"

    # Get base files
    base_files = list_base_renders()
    print(f"Found {len(base_files)} base render(s)")
    if not base_files:
        print("No base renders to process.")
        return

    # For auto batch, use the four standard modes
    lighting_modes = ["morning", "noon", "sunset", "night"]

    # Process each base file
    for base_file in base_files:
        base_name = os.path.splitext(os.path.basename(base_file))[0]
        print(f"\n[Processing] {base_name} (style: {style_name}, res: {resolution})")

        results = {}

        for mode in lighting_modes:
            print(f"  Generating {mode}...")
            try:
                # CURRENT SIGNATURE:
                # run_nano_variant(image_path, lighting_mode, style_name, resolution, output_folder=None)
                out_path = run_nano_variant(
                    image_path=base_file,
                    lighting_mode=mode,
                    style_name=style_name,
                    resolution=resolution,
                    output_folder=None,   # use default OUTPUT_FOLDER from agent_tools
                )
                results[mode] = out_path

                # log_result(base_name, lighting_mode, style_name, resolution, image_path)
                log_result(
                    base_name=base_name,
                    lighting_mode=mode,
                    style_name=style_name,
                    resolution=resolution,
                    image_path=out_path,
                )

            except Exception as e:
                print(f"  ERROR generating {mode}: {e}")
                results[mode] = None

    # Final summary
    check_output_folder()


def check_output_folder():
    """
    List images that were created in /output.
    """
    output_dir = "output"
    if not os.path.exists(output_dir):
        print("No output folder created.")
        return

    files = [
        f
        for f in os.listdir(output_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]
    if files:
        print("\n" + "=" * 60)
        print(f"Generated images in '{output_dir}' ({len(files)} total):")
        print("=" * 60)
        for f in sorted(files):
            print(f"  ✓ {f}")
    else:
        print("\nNo images generated yet.")


# --------------------------------------------------
# Main entry point
# --------------------------------------------------

def main():
    """
    Main entry point for running the batch agent with the current setup.
    """
    system_prompt = load_system_prompt()
    print("System prompt loaded.")

    base_files = list_base_renders()
    if not base_files:
        print("\n⚠️  WARNING: No base renders found in 'input' folder.")
        print("Please add at least one D5 render (PNG or JPG) to:")
        print("  C:\\Users\\cperez.PELLI\\Desktop\\Ai Agent\\input\\")
        print("\nThen run this script again.")
        return

    print(f"Found {len(base_files)} base render(s):")
    for f in base_files:
        print(f"  • {f}")

    print("\nTools wired to Gemini 3 Pro Image pipeline.")

    process_agent_task(system_prompt)

    print("\n✓ Agent run complete!")
    print("\nCheck your images in: C:\\Users\\cperez.PELLI\\Desktop\\Ai Agent\\output\\")


if __name__ == "__main__":
    main()
