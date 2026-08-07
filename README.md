# Kai Loop — SecondCrop MVP

The food waste problem we're tackling spans the whole supply chain. Our AI solution, Kai Loop, is a three-module platform for the Aotearoa AI Hackathon.

SecondCrop grades produce photos and routes each grade to
retail, processing, or rescue (KiwiHarvest).

## Structure
- frontend/ — React (Vite): upload, results, impact dashboard
- backend/  — FastAPI: /grade, /impact + SQLite log
- model/    — MobileNetV2 notebook + exported model
- data/     — produce images (gitignored)

## Team
- Samana — backend + model
- Hetvi  — frontend + mocked screens
