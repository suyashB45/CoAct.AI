@echo off
echo Starting CoAct.ai...

cd backend
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
echo Installing backend dependencies...
pip install -r requirements.txt
start "CoAct Backend" cmd /k "python app.py"

cd ..
echo Installing frontend dependencies...
call npm install
echo Starting Frontend...
start "CoAct Frontend" cmd /k "npm run dev"

echo Done! Both servers should be starting.
pause
