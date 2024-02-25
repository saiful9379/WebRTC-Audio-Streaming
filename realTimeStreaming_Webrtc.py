#!/usr/bin/env python3

import json
import ssl
import sys
import os
import concurrent.futures
import asyncio
import base64
import json
from flask import jsonify, Response
from urllib.request import urlopen
from urllib import request as rqst, parse
import urllib.error

from pathlib import Path
from aiohttp import web
from aiohttp.web_exceptions import HTTPServiceUnavailable
from aiortc import RTCSessionDescription, RTCPeerConnection
from av.audio.resampler import AudioResampler
import wave


ROOT = Path(__file__).parent

vosk_interface = os.environ.get('VOSK_SERVER_INTERFACE', '192.168.31.130')
vosk_port = int(os.environ.get('VOSK_SERVER_PORT', 5025))
vosk_model_path = os.environ.get('VOSK_MODEL_PATH', 'model')
vosk_cert_file = os.environ.get('VOSK_CERT_FILE', None)
vosk_key_file = os.environ.get('VOSK_KEY_FILE', None)
vosk_dump_file = os.environ.get('VOSK_DUMP_FILE', None)

pool = concurrent.futures.ThreadPoolExecutor((os.cpu_count() or 1))
dump_fd = None if vosk_dump_file is None else open(vosk_dump_file, "wb")
PREV_TEXT = ""

def process_chunk(rec, message):
    try:
        res = rec.AcceptWaveform(message)
    except Exception:
        result = None
    else:
        if res > 0:
            result = rec.Result()
        else:
            result = rec.PartialResult()
    return "Hello"


class AudioReciever:
    def __init__(self, user_connection):
        self.__resampler = AudioResampler(format='s16', layout='mono', rate=48000)
        self.__pc = user_connection
        self.__audio_task = None
        self.__track = None
        self.__channel = None
        self.audio_file_path = "audio_output.wav"
        self.audio_file = wave.open(self.audio_file_path, 'wb')
        self.audio_file.setnchannels(1)  # Mono channel
        self.audio_file.setsampwidth(2)  # 16-bit
        self.audio_file.setframerate(48000)  # Sample rate


    async def set_audio_track(self, track):
        self.__track = track

    async def set_text_channel(self, channel):
        self.__channel = channel

    async def start(self):
        self.__audio_task = asyncio.create_task(self.__run_audio_xfer())

    async def stop(self):
        if self.__audio_task is not None:
            self.__audio_task.cancel()
            self.__audio_task = None

            if self.audio_file is not None:
                self.audio_file.close()

    async def __run_audio_xfer(self):
        loop = asyncio.get_running_loop()

        max_frames = 20
        frames = []
        while True:
            fr = await self.__track.recv()
            frames.append(fr)

            # We need to collect frames so we don't send partial results too often
            if len(frames) < max_frames:
               continue

            dataframes = bytearray(b'')
            for fr in frames:
                for rfr in self.__resampler.resample(fr):
                    dataframes += bytes(rfr.planes[0])[:rfr.samples * 2]
            frames.clear()

            if dump_fd != None:
                dump_fd.write(bytes(dataframes))
            
            self.audio_file.writeframesraw(dataframes)

            # result = await loop.run_in_executor(pool, process_chunk, "", bytes(dataframes))
            # self.__channel.send(result)

async def index(request):
    content = open(str(ROOT / 'static' / 'index.html')).read()
    return web.Response(content_type='text/html', text=content)

async def message(request):
    # pass
    dat = [{"bt": "Hola", "audio": ""}]
    return web.json_response(dat)


async def offer(request):

    params = await request.json()
    offer = RTCSessionDescription(
        sdp=params['sdp'],
        type=params['type'])

    pc = RTCPeerConnection()

    aud = AudioReciever(pc)

    @pc.on('datachannel')
    async def on_datachannel(channel):      
        channel.send('') # Dummy message to make the UI change to "Listening"
        await aud.set_text_channel(channel)
        await aud.start()

    @pc.on('iceconnectionstatechange')
    async def on_iceconnectionstatechange():
        if pc.iceConnectionState == 'failed':
            await pc.close()

    @pc.on('track')
    async def on_track(track):
        if track.kind == 'audio':
            await aud.set_audio_track(track)

        @track.on('ended')
        async def on_ended():
            await aud.stop()

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type='application/json',
        text=json.dumps({
            'sdp': pc.localDescription.sdp,
            'type': pc.localDescription.type
        }))


if __name__ == '__main__':

    if vosk_cert_file:
        ssl_context = ssl.SSLContext()
        ssl_context.load_cert_chain(vosk_cert_file, vosk_key_file)
    else:
        ssl_context = None

    app = web.Application()
    app.router.add_post('/offer', offer)

    app.router.add_get('/', index)
    app.router.add_get('/message', message)
    app.router.add_static('/static/', path=ROOT / 'static', name='static')

    web.run_app(app, host="192.168.31.130", port=vosk_port, ssl_context=ssl_context)
