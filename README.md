# 🎓 Student Grade & Report Card Generator

A clean, interactive **Streamlit** web application where students can enter their subject marks and immediately generate an official **Academic Report Card** featuring:

- **Percent Grade** (per-subject & overall percentage)
- **Letter Grade** (`A+` through `F` or standard `A–F` scale)
- **Pass / Fail Status** (subject-by-subject and final report card status)
- **Cumulative GPA** (4.0 scale) & optional credit-hour weighting
- **Downloadable Report Cards** (printable `.html` report card & `.csv` export)

---

## 📁 Project Structure

```text
.
├── app.py                        # Main Streamlit web application
├── grading.py                    # Core grade & report card calculation engine
├── requirements.txt              # Dependencies for local & Streamlit Cloud deployment
├── sample_marks.csv              # Example CSV for bulk subject upload
├── .streamlit/config.toml        # Streamlit theme configuration
├── .github/workflows/tests.yml   # GitHub Actions CI test workflow
└── tests/test_grading.py         # Unit tests for grading calculations
```

---

## 🚀 Run Locally

1. **Create and activate a virtual environment** (optional but recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the Streamlit web app**:
   ```bash
   streamlit run app.py
   ```
   Your browser will open automatically at `http://localhost:8501`.

---

## 🌐 Connect to GitHub & Deploy on Streamlit Community Cloud

Streamlit Community Cloud connects directly to your GitHub repository and hosts your website for free (automatically updating whenever you push changes to GitHub).

### Step 1: Push this Project to GitHub
1. Create a new repository on [GitHub](https://github.com/new) (for example, `student-report-card-generator`) — leave *"Initialize with README"* unchecked.
2. In your terminal inside this project folder, run:
   ```bash
   git add .
   git commit -m "Initial commit: Student Grade & Report Card Generator"
   git branch -M main
   git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPO_NAME>.git
   git push -u origin main
   ```

### Step 2: Connect GitHub to Streamlit Community Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with your **GitHub** account.
2. Click **Create app** (or **New app**).
3. Select your repository (`<YOUR_GITHUB_USERNAME>/<YOUR_REPO_NAME>`), branch (`main`), and set **Main file path** to:
   ```text
   app.py
   ```
4. Click **Deploy!** — within ~1 minute your live public website URL (`https://...streamlit.app`) will be ready to share with students.

---

## 🧪 Run Unit Tests

```bash
python3 -m unittest discover -s tests -v
```
