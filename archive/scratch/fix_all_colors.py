import os
import re

FRONTEND_SRC = r"p:\projects\AIRS\frontend\src"

REPLACEMENTS = {
    # Non-existent 50-step and other middle values
    r"slate-955": "slate-950",
    r"slate-850": "slate-800",
    r"slate-750": "slate-700",
    r"slate-655": "slate-600",
    r"slate-650": "slate-600",
    r"slate-555": "slate-500",
    r"slate-550": "slate-500",
    r"slate-505": "slate-500",
    r"slate-455": "slate-400",
    r"slate-450": "slate-400",
    r"slate-405": "slate-400",
    r"slate-355": "slate-300",
    r"slate-350": "slate-300",
    r"slate-250": "slate-200",
    r"slate-205": "slate-200",
    r"slate-150": "slate-100",
    r"slate-905": "slate-900",
    r"slate-805": "slate-800",
    
    r"red-955": "red-950",
    r"orange-955": "orange-950",
    r"yellow-955": "yellow-950",
    r"green-955": "green-950",
    r"blue-955": "blue-950",
    r"amber-955": "amber-950",
    r"purple-955": "purple-950",
    r"emerald-955": "emerald-950",
    r"violet-955": "violet-950",
    
    r"violet-55": "violet-50",
    r"primary-605": "primary-600",
    r"primary-105": "primary-100",
    
    r"indigo-650": "indigo-600",
    r"indigo-550": "indigo-500",
    r"indigo-55": "indigo-50",
    r"blue-55": "blue-50",
    r"red-55": "red-50",
    r"red-655": "red-600",
    r"red-650": "red-600",
    r"orange-650": "orange-600",
    r"orange-105": "orange-100",
    r"yellow-650": "yellow-600",
    r"yellow-105": "yellow-100",
    r"green-650": "green-600",
    r"green-105": "green-100",
    r"purple-650": "purple-600",
    r"emerald-650": "emerald-600",
    r"emerald-605": "emerald-600",
    r"purple-705": "purple-700",
    r"amber-205": "amber-200",
    r"amber-805": "amber-800",
    r"blue-55/10": "blue-50/10",
    r"red-55/10": "red-50/10",
    
    r"blue-150": "blue-100",
    r"green-150": "green-100",
    r"amber-150": "amber-100",
    r"orange-150": "orange-100",
    r"purple-150": "purple-100",
}

def clean_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    original = content
    for pattern, replacement in REPLACEMENTS.items():
        # Match whole word patterns or patterns with opacity
        content = re.sub(r"\b" + pattern + r"\b", replacement, content)
        
    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Cleaned: {filepath}")

def main():
    for root, dirs, files in os.walk(FRONTEND_SRC):
        for file in files:
            if file.endswith((".tsx", ".ts", ".css")):
                clean_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
