from agent_tools import list_base_renders, run_nano_variant

LIGHTING_MODES = ["morning", "noon", "sunset", "night"]


def main():
    images = list_base_renders()
    if not images:
        print("No input images found in the 'input' folder.")
        return

    print("Found images:")
    for img in images:
        print(" -", img)

    for img in images:
        for mode in LIGHTING_MODES:
            print(f"\nProcessing {img} with lighting mode: {mode}")
            out = run_nano_variant(img, mode)
            print("Result placeholder:", out)


if __name__ == "__main__":
    main()
