#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$(dirname "$0")"

if ! command -v python >/dev/null 2>&1; then
    echo "Python is missing. On Termux, run: pkg install python"
    exit 1
fi

python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo
echo "Installation complete."
echo "Run the tool with: source .venv/bin/activate && python main.py"
