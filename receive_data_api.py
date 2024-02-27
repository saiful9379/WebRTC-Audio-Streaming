# from flask import Flask, request, jsonify
# import base64
# import os

# app = Flask(__name__)

# @app.route('/convert_audio', methods=['POST'])
# def convert_audio():
#     # Receive the audio file as a base64 encoded string

#     print("request:", request)
#     audio_base64 = request.json.get('audio')

#     print("audio data : ", audio_base64)
    
#     # Decode the base64 string to bytes
#     audio_bytes = base64.b64decode(audio_base64)
    
#     # Save the audio bytes to a file
#     # audio_file_path = 'received_audio.wav'
#     # with open(audio_file_path, 'wb') as f:
#     #     f.write(audio_bytes)
    
#     # Perform audio conversion here (if needed)
#     # For example, you could use a library like librosa for audio processing
    
#     # Return a response indicating success
#     return jsonify({'message': 'Audio received and saved successfully'})

# if __name__ == '__main__':
#     app.run(debug=True, host="192.168.10.72")


from flask import Flask, request, jsonify
import wave

app = Flask(__name__)

@app.route('/convert_audio', methods=['POST'])
def convert_audio():
    audio_data = request.data
    print(audio_data)

    return jsonify({'message': 'Audio received and saved successfully'})

if __name__ == '__main__':
    app.run(debug=True, host="192.168.10.72")