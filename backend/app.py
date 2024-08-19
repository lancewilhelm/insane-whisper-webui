from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
from transcription import transcribe_audio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

UPLOAD_FOLDER = 'uploads'
TRANSCRIPT_FOLDER = 'transcripts'
for folder in [UPLOAD_FOLDER, TRANSCRIPT_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Get HF token from environment variable
HF_TOKEN = os.getenv('HF_TOKEN')
if not HF_TOKEN:
    raise ValueError("HF_TOKEN not set in environment variables")


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_file(os.path.join(app.static_folder, 'index.html'))


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Get transcription options from the request
        model_name = request.form.get('model_name', 'openai/whisper-large-v3')
        diarization_model = request.form.get(
            'diarization_model', 'pyannote/speaker-diarization-3.1')
        num_speakers = request.form.get('num_speakers')
        min_speakers = request.form.get('min_speakers')
        max_speakers = request.form.get('max_speakers')
        device_id = request.form.get('device_id', '0')

        # Prepare diarization options
        diarization_options = {}
        if num_speakers:
            diarization_options['num_speakers'] = int(num_speakers)
        elif min_speakers and max_speakers:
            diarization_options['min_speakers'] = int(min_speakers)
            diarization_options['max_speakers'] = int(max_speakers)

        # Perform transcription with the specified options
        transcript = transcribe_audio(
            file_path, model_name, diarization_model, diarization_options, HF_TOKEN, device_id)

        transcript_filename = f"{os.path.splitext(filename)[0]}.json"
        transcript_path = os.path.join(TRANSCRIPT_FOLDER, transcript_filename)
        with open(transcript_path, 'w') as f:
            json.dump(transcript, f)

        return jsonify({
            'message': 'File uploaded and transcribed successfully',
            'filename': filename,
            'transcript_filename': transcript_filename
        })


@app.route('/files', methods=['GET'])
def list_files():
    files = []
    for filename in os.listdir(UPLOAD_FOLDER):
        transcript_filename = f"{os.path.splitext(filename)[0]}.json"
        transcript_path = os.path.join(TRANSCRIPT_FOLDER, transcript_filename)
        files.append({
            'filename': filename,
            'has_transcript': os.path.exists(transcript_path)
        })
    return jsonify(files)


@app.route('/transcript/<filename>', methods=['GET'])
def get_transcript(filename):
    transcript_path = os.path.join(TRANSCRIPT_FOLDER, filename)
    if os.path.exists(transcript_path):
        return send_file(transcript_path)
    else:
        return jsonify({'error': 'Transcript not found'}), 404


@app.route('/retranscribe/<filename>', methods=['POST'])
def retranscribe_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    # Get transcription options from the request
    model_name = request.form.get('model_name', 'openai/whisper-large-v3')
    diarization_model = request.form.get(
        'diarization_model', 'pyannote/speaker-diarization-3.1')
    num_speakers = request.form.get('num_speakers')
    min_speakers = request.form.get('min_speakers')
    max_speakers = request.form.get('max_speakers')
    device_id = request.form.get('device_id', '0')

    # Prepare diarization options
    diarization_options = {}
    if num_speakers:
        diarization_options['num_speakers'] = int(num_speakers)
    elif min_speakers and max_speakers:
        diarization_options['min_speakers'] = int(min_speakers)
        diarization_options['max_speakers'] = int(max_speakers)

    # Perform transcription with the specified options
    transcript = transcribe_audio(
        file_path, model_name, diarization_model, diarization_options, HF_TOKEN, device_id)

    transcript_filename = f"{os.path.splitext(filename)[0]}.json"
    transcript_path = os.path.join(TRANSCRIPT_FOLDER, transcript_filename)
    with open(transcript_path, 'w') as f:
        json.dump(transcript, f)

    return jsonify({
        'message': 'File re-transcribed successfully',
        'filename': filename,
        'transcript_filename': transcript_filename
    })


@app.route('/rename', methods=['POST'])
def rename_file():
    data = request.json
    old_filename = data.get('old_filename')
    new_filename = data.get('new_filename')

    if not old_filename or not new_filename:
        return jsonify({'error': 'Both old and new filenames are required'}), 400

    old_file_path = os.path.join(UPLOAD_FOLDER, old_filename)
    new_file_path = os.path.join(UPLOAD_FOLDER, new_filename)

    if not os.path.exists(old_file_path):
        return jsonify({'error': 'File not found'}), 404

    if os.path.exists(new_file_path):
        return jsonify({'error': 'A file with the new name already exists'}), 400

    try:
        # Rename the audio file
        os.rename(old_file_path, new_file_path)

        # Rename the transcript file if it exists
        old_transcript_filename = f"{os.path.splitext(old_filename)[0]}.json"
        new_transcript_filename = f"{os.path.splitext(new_filename)[0]}.json"
        old_transcript_path = os.path.join(
            TRANSCRIPT_FOLDER, old_transcript_filename)
        new_transcript_path = os.path.join(
            TRANSCRIPT_FOLDER, new_transcript_filename)

        if os.path.exists(old_transcript_path):
            os.rename(old_transcript_path, new_transcript_path)

        return jsonify({'message': 'File renamed successfully', 'new_filename': new_filename})
    except Exception as e:
        return jsonify({'error': f'Failed to rename file: {str(e)}'}), 500


@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    transcript_filename = f"{os.path.splitext(filename)[0]}.json"
    transcript_path = os.path.join(TRANSCRIPT_FOLDER, transcript_filename)

    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    try:
        # Delete the audio file
        os.remove(file_path)

        # Delete the transcript file if it exists
        if os.path.exists(transcript_path):
            os.remove(transcript_path)

        return jsonify({'message': 'File and associated transcript deleted successfully'})
    except Exception as e:
        return jsonify({'error': f'Failed to delete file: {str(e)}'}), 500


@app.route('/update_speaker_names', methods=['POST'])
def update_speaker_names():
    data = request.json
    transcript_filename = data.get('transcript_filename')
    speaker_names = data.get('speaker_names')

    if not transcript_filename or not speaker_names:
        return jsonify({'error': 'Transcript filename and speaker names are required'}), 400

    transcript_path = os.path.join(TRANSCRIPT_FOLDER, transcript_filename)

    if not os.path.exists(transcript_path):
        return jsonify({'error': 'Transcript not found'}), 404

    try:
        with open(transcript_path, 'r') as f:
            transcript = json.load(f)

        for segment in transcript['speakers']:
            if segment['speaker'] in speaker_names:
                segment['speaker'] = speaker_names[segment['speaker']]

        with open(transcript_path, 'w') as f:
            json.dump(transcript, f)

        return jsonify({'message': 'Speaker names updated successfully'})
    except Exception as e:
        return jsonify({'error': f'Failed to update speaker names: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
