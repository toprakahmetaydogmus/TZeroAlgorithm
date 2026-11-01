import json

def main():
    with open("benchmark-site/cortex_caps.json", "r", encoding="utf-8") as f:
        caps = json.load(f)

    with open("benchmark-site/cortex_module.js", "r", encoding="utf-8") as f:
        module_js = f.read()

    combined_js = (
        "\n// ==========================================\n"
        "// 6. T-ZERO NEURAL CORTEX & 105 MATRIX LAB\n"
        "// ==========================================\n"
        "const CORTEX_CAPABILITIES = " + json.dumps(caps, ensure_ascii=False, indent=2) + ";\n\n"
        + module_js
    )

    with open("benchmark-site/app.js", "r", encoding="utf-8") as f:
        app_js = f.read()

    if "initNeuralCortex" not in app_js:
        app_js += combined_js
        with open("benchmark-site/app.js", "w", encoding="utf-8") as f:
            f.write(app_js)
        print("Successfully merged and appended Neural Cortex to app.js!")
    else:
        # If it was already present or partially present, ensure it has the latest combined_js
        idx = app_js.find("// 6. T-ZERO NEURAL CORTEX & 105 MATRIX LAB")
        if idx != -1:
            app_js = app_js[:idx] + combined_js
            with open("benchmark-site/app.js", "w", encoding="utf-8") as f:
                f.write(app_js)
            print("Successfully updated Neural Cortex in app.js!")
        else:
            app_js += combined_js
            with open("benchmark-site/app.js", "w", encoding="utf-8") as f:
                f.write(app_js)
            print("Appended combined Neural Cortex to app.js!")

if __name__ == "__main__":
    main()
