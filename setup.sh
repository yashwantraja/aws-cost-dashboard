#!/bin/bash
# AWS Cost Dashboard Setup Script
# Usage: chmod +x setup.sh && ./setup.sh

echo "☁️ AWS Cost Dashboard Setup"
echo "============================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 To run the dashboard:"
echo "   source venv/bin/activate"
echo "   streamlit run aws_cost_dashboard.py"
echo ""
echo "🌐 The dashboard will be available at: http://localhost:8501"
echo ""
