
from flask import Flask, request, jsonify
import wave

app = Flask(__name__)


import os
import numpy as np
from array import array
from struct import pack
from sys import byteorder
import copy
import pyaudio
import wave, time
import matplotlib.pyplot as plt
import IPython.display as ipd
from IPython.display import display, Audio


THRESHOLD = 500  # audio levels not normalised.
CHUNK_SIZE = 1024
SILENT_CHUNKS = 1 * 16000 / 1024  # about 10 sec
FORMAT = pyaudio.paInt16
FRAME_MAX_VALUE = 2 ** 15 - 1
NORMALIZE_MINUS_ONE_dB = 1 ** (-1.0 / 20)
RATE = 16000
CHANNELS = 1
TRIM_APPEND = RATE / 4

# p = pyaudio.PyAudio()

def is_silent(data_chunk):
    """Returns 'True' if below the 'silent' threshold"""
    return max(data_chunk) < THRESHOLD

def normalize(data_all):
    """Amplify the volume out to max -1dB"""
    # MAXIMUM = 16384
    normalize_factor = (float(NORMALIZE_MINUS_ONE_dB * FRAME_MAX_VALUE)
                        / max(abs(i) for i in data_all))

    r = array('h')
    for i in data_all:
        r.append(int(i * normalize_factor))
    return r



def trim(data_all):

    _from = 0
    _to = len(data_all) - 1
    for i, b in enumerate(data_all):
        if abs(b) > THRESHOLD:
            _from = max(0, i - int(TRIM_APPEND))
            break

    for i, b in enumerate(reversed(data_all)):
        if abs(b) > THRESHOLD:
            _to = min(len(data_all) - 1, len(data_all) - 1 - i + int(TRIM_APPEND))
            break

    return copy.deepcopy(data_all[_from:(_to + 1)])


class RecordClass:
    def __init__(self) -> None:
        self.data_all = array('h')
        self.audio_started = False
        self.silent_chunks = 0
        self.n_all_data = array('h')
        self.break_status = False
        self.increments= 0
        

    def record(self, data):
        """Record a word or words from the microphone and
        return the data as an array of signed shorts."""

        # silent_chunks = 0
        # audio_started = False
        # data_all = array('h')

        # while True:

        # data = data
        # little endian, signed short
        data_chunk = array('h', data)
        if byteorder == 'big':
            data_chunk.byteswap()

        # self.data_all.extend(data_chunk)

        silent = is_silent(data_chunk)

        if self.audio_started:
            if silent:
                self.silent_chunks += 1
                if self.silent_chunks > SILENT_CHUNKS:
                    print("silent chunks: ",self.silent_chunks, "silent threshold : ", SILENT_CHUNKS)
                    print("================ break data==============================")

                    # self.n_all_data = array('h')
                    self.silent_chunks = 0
                    self.break_status = True
            else:
                print("="*40)
                print("not silent into audio_started")
                # print("every silent : ", data_chunk)
                print("insert lenght : ", len(self.n_all_data))
                self.n_all_data.extend(data_chunk)
                # print("data lenght : ", len(self.data_all))
                self.break_status = False
                self.silent_chunks = 0
                print("="*40)

        elif not silent:
            print("not silent")
            self.n_all_data.extend(data_chunk)
            self.break_status = False
            self.audio_started = True

        sample_width = 48000

        # stream.stop_stream()
        # stream.close()
        # p.terminate()
            
        if self.break_status and len(self.n_all_data)!=0:
            self.increments += 1

            print("==== empty lenght : ", len(self.n_all_data))
            # print(self.n_all_data)

            # data_all = trim(self.n_all_data)

            data = trim(self.n_all_data)  
            # We trim before normalize as threshhold applies to un-normalized wave (as well as is_silent() function)
            data_all = normalize(data)

            data = pack('<' + ('h' * len(data_all)), *data_all)

            print("data_all", type(data_all))

            print(data_all)


            print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

            # audio_np = np.array(data)
            # audio_np = audio_np.astype(np.float32)


            print("filtered : ", data)

            self.n_all_data = array('h')

            # exit()

            # print("=====number of lenght :", len(self.n_all_data))
            file_path = os.path.join("logs", f'audio_output_{self.increments}.wav')
            wave_file = wave.open(file_path, 'wb')
            wave_file.setnchannels(CHANNELS)
            wave_file.setsampwidth(2)
            wave_file.setframerate(sample_width)
            wave_file.writeframes(data)
            wave_file.close()

        return 


recoder_obj = RecordClass()


@app.route('/convert_audio', methods=['POST'])

def convert_audio():
    audio_data = request.data
    # print(audio_data)

    recoder_obj.record(audio_data)



    return jsonify({'message': 'Audio received and saved successfully'})

if __name__ == '__main__':
    app.run(debug=True, host="192.168.10.72")