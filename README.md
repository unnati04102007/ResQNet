# ResQNet - Emergency Response & Donation Management System

A modern web application built with Flask and SQLite for emergency response coordination and donation management.

## 🚀 Features

- **Emergency Reporting**: Report disasters and emergencies with location tracking
- **Donation Management**: Secure donation system with multiple payment gateways
- **Volunteer Coordination**: Connect volunteers with emergency response teams
- **Real-time Dashboard**: Monitor emergency situations and resource allocation
- **Modern UI**: Beautiful, responsive design with animations

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite3
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Styling**: Custom CSS with animations and responsive design
- **API**: RESTful API with JSON responses

## 📁 Project Structure

```
ResQNet/
├── .vscode/                 # VS Code configuration
│   ├── launch.json         # Debug configurations
│   ├── settings.json       # Workspace settings
│   ├── tasks.json          # Build tasks
│   └── extensions.json     # Recommended extensions
├── static/
│   └── style.css           # Main stylesheet
├── templates/
│   └── index.html          # Main HTML template
├── app.py                  # Flask application
├── donations.db            # SQLite database
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ResQNet
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open your browser**
   ```
   http://localhost:5000
   ```

## 🔧 Development

### VS Code Setup

1. Open the project in VS Code
2. Install recommended extensions (Python, Flask, etc.)
3. Select the Python interpreter: `./venv/Scripts/python.exe`
4. Press `F5` to run with debugging

### Available Tasks

- **Run Flask App**: Start the development server
- **Install Dependencies**: Install Python packages
- **Format Code**: Format code with Black
- **Run Tests**: Execute test suite

### API Endpoints

- `GET /` - Main donation page
- `POST /api/donate` - Submit a donation
- `GET /api/get-donations` - Retrieve all donations

### Database Schema

```sql
CREATE TABLE donations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_name TEXT NOT NULL,
    donor_email TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount > 0),
    currency TEXT NOT NULL DEFAULT 'USD',
    purpose TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🎨 UI Features

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Modern Animations**: Smooth transitions and hover effects
- **Interactive Forms**: Real-time validation and feedback
- **Live Updates**: Donations list updates automatically
- **Error Handling**: User-friendly error messages

## 📱 Screenshots

The application features a modern, gradient-based design with:
- Clean donation form with amount selection buttons
- Real-time donations list with card-based layout
- Responsive navigation and mobile-friendly interface
- Professional color scheme and typography

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/your-repo/issues) page
2. Create a new issue with detailed information
3. Contact the development team

## 🔮 Future Enhancements

- [ ] User authentication and authorization
- [ ] Payment gateway integration (Stripe, PayPal, Razorpay)
- [ ] Real-time notifications
- [ ] Mobile app development
- [ ] Advanced reporting and analytics
- [ ] Multi-language support
- [ ] Admin dashboard
- [ ] Email notifications
- [ ] SMS alerts
- [ ] Map integration for emergency locations

---

**Built with ❤️ for emergency response and community support**

