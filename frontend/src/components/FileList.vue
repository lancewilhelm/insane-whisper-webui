<template>
  <div class="flex">
    <div v-if="files.length === 0" class="text-gray-500 flex">No files uploaded yet.</div>
    <ul v-else class="space-y-4 flex flex-col flex-grow">
      <li v-for="file in files" :key="file.filename"
        :class="['shadow rounded-lg p-4 flex justify-center', file.filename === currentFile ? 'bg-green-200' : 'bg-slate-200']">
        <div class="flex flex-col items-center flex-1">
          <div v-if="editingFile === file.filename">
            <input v-model="newFileName" @keyup.enter="renameFile(file.filename)" @blur="cancelRename"
              class="border p-1 rounded" ref="renameInput">
          </div>
          <span v-else class="font-medium">{{ file.filename }}</span>
          <div class="grid gap-2 grid-cols-2">
            <button v-if="file.has_transcript" @click="viewTranscript(file.filename)"
              class="bg-blue-500 hover:bg-blue-600 text-white font-bold w-8 h-8 rounded">
              <FontAwesomeIcon icon='fa-regular fa-file-lines' />
            </button>
            <button @click="openRetranscribeModal(file.filename)"
              :class="['font-bold w-8 h-8 rounded', file.has_transcript ? 'bg-green-500 hover:bg-green-600 text-white' : 'bg-yellow-500 hover:bg-yellow-600 text-white']">
              <FontAwesomeIcon icon="fa-solid fa-rotate" />
            </button>
            <button @click="startRename(file.filename)"
              class="bg-gray-500 hover:bg-gray-600 text-white font-bold w-8 h-8 rounded">
              <FontAwesomeIcon icon="fa-solid fa-signature" />
            </button>
            <button @click="confirmDelete(file.filename)"
              class="bg-red-500 hover:bg-red-600 text-white font-bold w-8 h-8 rounded">
              <FontAwesomeIcon icon="fa-solid fa-trash-can" />
            </button>
          </div>
        </div>
      </li>
    </ul>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal"
      class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center">
      <div class="bg-white p-5 rounded-lg shadow-xl">
        <h3 class="text-lg font-semibold mb-4">Confirm Deletion</h3>
        <p>Are you sure you want to delete {{ fileToDelete }}?</p>
        <div class="mt-4 flex justify-end space-x-3">
          <button @click="showDeleteModal = false"
            class="bg-gray-300 hover:bg-gray-400 text-black font-bold py-2 px-4 rounded">
            Cancel
          </button>
          <button @click="deleteFile" class="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded">
            Delete
          </button>
        </div>
      </div>
    </div>

    <!-- Re-transcribe Options Modal -->
    <div v-if="showRetranscribeModal"
      class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center">
      <div class="bg-white p-5 rounded-lg shadow-xl max-w-md w-full">
        <h3 class="text-lg font-semibold mb-4">Re-transcribe Options</h3>
        <div class="mb-4">
          <label class="block mb-2">Model Name:</label>
          <input v-model="retranscribeOptions.modelName" class="w-full p-2 border rounded"
            placeholder="e.g., openai/whisper-large-v3">
        </div>
        <div class="mb-4">
          <label class="block mb-2">Diarization Model:</label>
          <input v-model="retranscribeOptions.diarizationModel" class="w-full p-2 border rounded"
            placeholder="e.g., pyannote/speaker-diarization-3.1">
        </div>
        <div class="mb-4">
          <label class="block mb-2">Number of Speakers:</label>
          <input v-model.number="retranscribeOptions.numSpeakers" type="number" class="w-full p-2 border rounded"
            min="1">
        </div>
        <div class="mb-4">
          <label class="block mb-2">Min Speakers:</label>
          <input v-model.number="retranscribeOptions.minSpeakers" type="number" class="w-full p-2 border rounded"
            min="1">
        </div>
        <div class="mb-4">
          <label class="block mb-2">Max Speakers:</label>
          <input v-model.number="retranscribeOptions.maxSpeakers" type="number" class="w-full p-2 border rounded"
            min="1">
        </div>
        <div class="flex justify-end space-x-3">
          <button @click="showRetranscribeModal = false"
            class="bg-gray-300 hover:bg-gray-400 text-black font-bold py-2 px-4 rounded">
            Cancel
          </button>
          <button @click="confirmRetranscribe"
            class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded">
            Re-transcribe
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
import axios from 'axios';

const files = ref([]);
const editingFile = ref(null);
const currentFile = ref(null);
const newFileName = ref('');
const showDeleteModal = ref(false);
const fileToDelete = ref(null);
const renameInput = ref(null);
const showRetranscribeModal = ref(false);
const fileToRetranscribe = ref(null);
const retranscribeOptions = ref({
  modelName: 'openai/whisper-large-v3',
  diarizationModel: 'pyannote/speaker-diarization-3.1',
  numSpeakers: null,
  minSpeakers: null,
  maxSpeakers: null
});

const openRetranscribeModal = (filename) => {
  fileToRetranscribe.value = filename;
  showRetranscribeModal.value = true;
};

const confirmRetranscribe = async () => {
  showRetranscribeModal.value = false;
  await retranscribe(fileToRetranscribe.value);
};

const emit = defineEmits(['show-transcript']);

const fetchFiles = async () => {
  try {
    const response = await axios.get('http://' + import.meta.env.VITE_APP_BACKEND_URL + '/files');
    files.value = response.data;
  } catch (error) {
    console.error('Error fetching files:', error);
  }
};

const viewTranscript = async (filename) => {
  try {
    // Remove the file extension for the transcript request
    const baseFilename = filename.split('.').slice(0, -1).join('.');

    const response = await axios.get('http://' + import.meta.env.VITE_APP_BACKEND_URL + '/transcript/' + baseFilename + '.json', {
      responseType: 'json'
    });

    emit('show-transcript', {
      transcript: response.data,
      filename: filename  // Keep the full filename for other purposes
    });

    currentFile.value = filename;

  } catch (error) {
    console.error('Error fetching transcript:', error);
    alert('Failed to fetch transcript. Please try again.');
  }
};

const retranscribe = async (filename) => {
  try {
    const formData = new FormData();
    formData.append('model_name', retranscribeOptions.value.modelName);
    formData.append('diarization_model', retranscribeOptions.value.diarizationModel);
    if (retranscribeOptions.value.numSpeakers) formData.append('num_speakers', retranscribeOptions.value.numSpeakers);
    if (retranscribeOptions.value.minSpeakers) formData.append('min_speakers', retranscribeOptions.value.minSpeakers);
    if (retranscribeOptions.value.maxSpeakers) formData.append('max_speakers', retranscribeOptions.value.maxSpeakers);

    await axios.post('http://' + import.meta.env.VITE_APP_BACKEND_URL + '/retranscribe/' + filename, formData);
    alert('Transcription completed successfully.');
    await fetchFiles(); // Refresh the file list
    viewTranscript(filename);
  } catch (error) {
    console.error('Error re-transcribing file:', error);
    alert('Failed to re-transcribe file. Please try again.');
  }
};

// Update the existing retranscribe button click handler
const handleRetranscribeClick = (filename) => {
  openRetranscribeModal(filename);
};

const startRename = (filename) => {
  editingFile.value = filename;
  newFileName.value = filename;
  nextTick(() => {
    renameInput.value?.focus();
  });
};

const renameFile = async (oldFilename) => {
  try {
    await axios.post('http://' + import.meta.env.VITE_APP_BACKEND_URL + '/rename', {
      old_filename: oldFilename,
      new_filename: newFileName.value
    });
    editingFile.value = null;
    await fetchFiles(); // Refresh the file list
  } catch (error) {
    console.error('Error renaming file:', error);
    alert('Failed to rename file. Please try again.');
  }
};

const cancelRename = () => {
  editingFile.value = null;
};

const confirmDelete = (filename) => {
  fileToDelete.value = filename;
  showDeleteModal.value = true;
};

const deleteFile = async () => {
  try {
    await axios.delete('http://' + import.meta.env.VITE_APP_BACKEND_URL + '/delete/' + fileToDelete.value);
    showDeleteModal.value = false;
    fileToDelete.value = null;
    await fetchFiles(); // Refresh the file list
  } catch (error) {
    console.error('Error deleting file:', error);
    alert('Failed to delete file. Please try again.');
  }
};

onMounted(fetchFiles);
</script>
