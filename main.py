import re
from fastapi import FastAPI, UploadFile, File, status, Body
from numpy import save
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import time
import os
import scipy.io.wavfile as sc
from math import cos, sin
import numpy as np
from fastapi.responses import JSONResponse

stereo_methods = {
    "XY": {
        "mic1_angle": -45,
        "mic1_polarity": 0.5,
        "mic1_label": "L",
        "mic2_angle": 45,
        "mic2_polarity": 0.5,
        "mic2_label": "P",
    },
    "Blumlein": {
        "mic1_angle": -45,
        "mic1_polarity": 0,
        "mic1_label": "L",
        "mic2_angle": 45,
        "mic2_polarity": 0,
        "mic2_label": "P",
    },
    "MS": {
        "mic1_angle": 0,
        "mic1_polarity": 0.5,
        "mic1_label": "Mid",
        "mic2_angle": 90,
        "mic2_polarity": 0,
        "mic2_label": "Side",
    }
}

app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_200_OK, content = {"message": "Hello World"})


@app.post("/savefile")
async def save_file(file: UploadFile = File(...)) -> JSONResponse:
    if file.filename.split(".")[-1] != "wav":
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content = {"message": "Wrong file format!"})
    dir_path = os.path.dirname(os.path.realpath(__file__))
    filename_absolute = f'{dir_path}/inputfiles/{file.filename}'
    f = open(f'{filename_absolute}', 'wb')
    content = await file.read()
    f.write(content)

    return JSONResponse(status_code=status.HTTP_200_OK, content = {"message": f"File {file.filename} loaded."})

class Mono(BaseModel):
    filename: str
    theta: str
    p: str
    format: str


@app.post("/convertmono")
async def convert_mono(mono: Mono = Body(...)) -> JSONResponse:
    
    response = ambisonic_to_mono(mono.filename, mono.theta, mono.p, "Mono", mono.format)

    if response.status_code != 200:
        return response

    return JSONResponse(status_code=status.HTTP_200_OK, content = {"filenames": [f"Mono_{mono.filename}"], "message": "Ready to download"})


class Stereo(BaseModel):
    filename: str
    method: str
    format: str


@app.post("/convertstereo")
async def convert_stereo(stereo: Stereo = Body(...)) -> JSONResponse:
    
    method = stereo.method

    theta_1 = stereo_methods[method]["mic1_angle"]
    p_1 = stereo_methods[method]["mic1_polarity"]
    label_1 = stereo_methods[method]["mic1_label"]

    response = ambisonic_to_mono(stereo.filename, theta_1, p_1, label_1, stereo.format)

    if response.status_code != 200:
        return response

    theta_2 = stereo_methods[method]["mic2_angle"]
    p_2 = stereo_methods[method]["mic2_polarity"]
    label_2 = stereo_methods[method]["mic2_label"]

    response = ambisonic_to_mono(stereo.filename, theta_2, p_2, label_2, stereo.format)

    if response.status_code != 200:
        return response

    return JSONResponse(status_code=status.HTTP_200_OK, content = {"filenames": [f"{label_1}_{stereo.filename}", f"{label_2}_{stereo.filename}"], "message": "Ready to download"})


def ambisonic_to_mono(filename: str, theta: str, p: str, label: str, format: str) -> JSONResponse:
    # first mic
    theta = int(theta)
    p = int(p) / 100

    filename_absolute = f'{os.path.dirname(os.path.realpath(__file__))}/inputfiles/{filename}'

    theta_rad = (theta * 180) / 3.1415
    cosine = round(cos(theta_rad), 2)
    sine = round(sin(theta_rad), 2)
    try:
        samplerate, data = sc.read(f"{filename_absolute}")
    except:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content = {"message": "Loading error, please refresh site"})

    if data.size > 5_292_000:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content = {"message": "File too large"})
    if data.dtype != np.int16:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content = {"message": "Wrong bitrate"})
    if data[0].size != 4:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content = {"message": "Not a 4-channel recording"})

    out = np.array([0]*(data.size // 4), dtype = np.int16)

    if format == "ambix":
        for i, (W, X, Y, _) in enumerate(data):
            out[i] = p * 0.7 * W + (1 - p) * (cosine*X + sine*Y)
    elif format == "fuma":
        for i, (W, Y, _, X) in enumerate(data):
            out[i] = p * 0.7 * W + (1 - p) * (cosine*X + sine*Y)
    else:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return save_wav(np.array(out), filename, samplerate, label)


def save_wav(data: list[float], filename: str, samplerate: int, label: str) -> JSONResponse:
    dir_path = os.path.dirname(os.path.realpath(__file__))
    filename_abolute = f'{dir_path}/outputfiles/{label}_{filename}'

    try:
        sc.write(filename_abolute, samplerate, data.astype(np.int16)) 
    except:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JSONResponse(status_code=status.HTTP_200_OK)