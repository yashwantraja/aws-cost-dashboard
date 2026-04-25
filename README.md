# AWS Cost Explorer Dashboard

☁️ A beautiful, interactive Streamlit dashboard for AWS cost analysis and comparison.

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![AWS](https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://aws.amazon.com)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

![Dashboard Preview](https://img.shields.io/badge/Dashboard-Dark%20Theme-161b22?style=for-the-badge)

## ✨ Features

- **📊 Cost Comparison**: Compare costs between any two months side-by-side
- **📈 Interactive Charts**: Beautiful Plotly visualizations with dark theme
- **🔍 Service Analysis**: Deep dive into individual service costs
- **📅 Monthly Trends**: Track cost patterns over time
- **🏷️ Tag Filtering**: Filter costs by tags (Environment, Team, Project, etc.)
- **🌍 Regional Breakdown**: Analyze costs by AWS region
- **🛒 Marketplace Charges**: Separate tracking of third-party charges
- **⚠️ Anomaly Detection**: View AWS Cost Anomaly alerts
- **📧 Email Reports**: Export and email cost reports automatically
- **🎨 Dark Theme**: Professional GitHub-inspired dark UI

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- AWS Account with Cost Explorer access
- (Optional) Gmail account for email reports

### Installation

```bash
# Clone the repository
git clone https://github.com/yashwantraja/aws-cost-dashboard.git
cd aws-cost-dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run aws_cost_dashboard.py
```

## 🔐 AWS Setup

### Required IAM Permissions

Your AWS credentials need these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ce:GetCostAndUsage",
                "ce:GetCostForecast",
                "ce:GetAnomalies",
                "ce:ListCostAllocationTags",
                "ce:GetTags",
                "ce:GetDimensionValues"
            ],
            "Resource": "*"
        }
    ]
}
```

### Getting AWS Credentials

1. Go to AWS Console → IAM → Users
2. Select your user → Security credentials
3. Click "Create access key"
4. Copy Access Key ID and Secret Access Key

## 📧 Email Setup (Optional)

To enable email reports:

1. Go to [Google Account App Passwords](https://myaccount.google.com/apppasswords)
2. Generate a 16-character app password
3. Use this password (not your regular Gmail password) in the dashboard

## 📸 Dashboard Preview

### Cost Comparison View
- Side-by-side month comparison
- Difference highlighting with badges
- Percentage change indicators

### Service Analysis
- Top cost drivers identification
- Individual service deep-dive
- Sortable data tables

### Trend Analysis
- Monthly cost patterns
- Forecast visualization
- Historical comparison

### Tag-Based Filtering
- Filter by Environment (prod, dev, staging)
- Filter by Team or Project
- Custom tag support

## 🛠️ Technical Stack

- **Frontend**: [Streamlit](https://streamlit.io/) - Python-based web framework
- **Visualization**: [Plotly](https://plotly.com/python/) - Interactive charts
- **AWS Integration**: [Boto3](https://boto3.amazonaws.com/) - AWS SDK for Python
- **Styling**: Custom CSS with GitHub dark theme
- **Email**: SMTP with Gmail integration

## 📦 Project Structure

```
aws-cost-dashboard/
├── aws_cost_dashboard.py    # Main application
├── requirements.txt         # Python dependencies
├── README.md               # This file
└── .gitignore              # Git ignore rules
```

## 🌐 Deployment Options

### Local Development
```bash
streamlit run aws_cost_dashboard.py
```

### EC2 Deployment
```bash
# On Ubuntu EC2 instance
pip install -r requirements.txt
nohup streamlit run aws_cost_dashboard.py --server.port 8501 &
# Open port 8501 in security group
```

### Docker Deployment
```bash
docker build -t aws-cost-dashboard .
docker run -p 8501:8501 aws-cost-dashboard
```

## 🔒 Security Notes

- Credentials are used only for the current session
- No data is stored on disk
- AWS credentials are never logged
- For production, use IAM roles instead of access keys

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- AWS Cost Explorer API
- Streamlit community
- Plotly for beautiful visualizations

## 📧 Contact

**Yashwant Raja** - [@yashwantraja](https://github.com/yashwantraja)

Project Link: [https://github.com/yashwantraja/aws-cost-dashboard](https://github.com/yashwantraja/aws-cost-dashboard)

---

⭐ Star this repository if you find it helpful!
