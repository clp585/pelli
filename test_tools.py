from agent_tools import list_base_renders, run_nano_variant

def main():
    files = list_base_renders()
    print("Found base renders:", files)

    if not files:
        print("Put at least one image in the input folder first.")
        return

    first = files[0]
    print("Using first image:", first)

    for mode in ["morning", "noon", "sunset", "night"]:
        print(f"\nGenerating {mode} for {first}...")
        out_path = run_nano_variant(first, mode)
        print("Saved to:", out_path)

if __name__ == "__main__":
    main()
