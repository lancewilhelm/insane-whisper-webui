<template>
  <div class="mb-8">
    <h2 class="text-2xl font-semibold mb-4">Upload Audio File</h2>
    <div class="flex items-center space-x-4 mb-4">
      <label class="flex-1">
        <input type="file" @change="handleFileChange" accept="audio/*" class="hidden">
        <div class="bg-gray-200 hover:bg-gray-300 cursor-pointer rounded-lg p-4 text-center">
          {{ fileName || 'Choose a file' }}
        </div>
      </label>
    </div>

    <div class='grid grid-cols-4 gap-8'>
      <div class="mb-4">
        <label class="block mb-2">Model Name:</label>
        <input v-model="modelName" class="w-full p-2 border rounded" placeholder="e.g., openai/whisper-large-v3">
      </div>

      <div class="mb-4">
        <label class="block mb-2">Diarization Model:</label>
        <input v-model="diarizationModel" class="w-full p-2 border rounded"
          placeholder="e.g., pyannote/speaker-diarization">
      </div>

      <div class="mb-4">
        <label class="block mb-2">Diarization Options:</label>
        <div class="flex flex-col items-left">
          <label>
            <input type="radio" v-model="diarizationType" value="none"> None
          </label>
          <label>
            <input type="radio" v-model="diarizationType" value="num_speakers"> Number of Speakers
          </label>
          <label>
            <input type="radio" v-model="diarizationType" value="min_max_speakers"> Min/Max Speakers
          </label>
        </div>
      </div>

      <div v-if="diarizationType === 'num_speakers'" class="mb-4">
        <label class="block mb-2">Number of Speakers:</label>
        <input v-model.number="numSpeakers" type="number" min="1" class="w-full p-2 border rounded">
      </div>

      <div v-if="diarizationType === 'min_max_speakers'" class="mb-4 flex space-x-4">
        <div class="flex-1">
          <label class="block mb-2">Min Speakers:</label>
          <input v-model.number="minSpeakers" type="number" min="1" class="w-full p-2 border rounded">
        </div>
        <div class="flex-1">
          <label class="block mb-2">Max Speakers:</label>
          <input v-model.number="maxSpeakers" type="number" min="1" class="w-full p-2 border rounded">
        </div>
      </div>
    </div>

    <div class='flex'>
      <button @click="uploadFile" :disabled="!file"
        class="flex-1 bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded disabled:opacity-50 disabled:cursor-not-allowed">
        Upload
      </button>
    </div>

    <div v-if="isUploading" class="mt-4">
      <div class="bg-blue-100 text-blue-700 p-4 rounded">
        Uploading and transcribing... Please wait.
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'FileUploader',
  data() {
    return {
      file: null,
      fileName: '',
      isUploading: false,
      modelName: 'openai/whisper-large-v3',
      diarizationModel: 'pyannote/speaker-diarization',
      diarizationType: 'none',
      numSpeakers: 2,
      minSpeakers: 1,
      maxSpeakers: 5
    };
  },
  methods: {
    handleFileChange(event) {
      this.file = event.target.files[0];
      this.fileName = this.file ? this.file.name : '';
    },
    async uploadFile() {
      if (!this.file) return;

      this.isUploading = true;
      const formData = new FormData();
      formData.append('file', this.file);
      formData.append('model_name', this.modelName);
      formData.append('diarization_model', this.diarizationModel);

      if (this.diarizationType === 'num_speakers') {
        formData.append('num_speakers', this.numSpeakers);
      } else if (this.diarizationType === 'min_max_speakers') {
        formData.append('min_speakers', this.minSpeakers);
        formData.append('max_speakers', this.maxSpeakers);
      }

      try {
        const response = await axios.post('http://' + import.meta.env.VITE_APP_BACKEND_URL + '/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        this.$emit('file-uploaded', response.data);
      } catch (error) {
        console.error('Error uploading file:', error);
        alert('An error occurred while uploading the file. Please try again.');
      } finally {
        this.isUploading = false;
      }
    }
  }
}
</script>
