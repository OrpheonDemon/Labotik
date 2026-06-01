#!/usr/bin/env python
import os
import sys

# Set working directory
os.chdir('c:\\Users\\Rothe\\Rotherick\\Laboratorio\\backend')
sys.path.insert(0, os.getcwd())

# Run uvicorn
if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
