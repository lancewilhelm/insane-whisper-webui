<template>
  <div v-if="transcript" class="col-start-2 col-end-7">
    <div v-if="transcript.speakers && transcript.speakers.length > 0" class="mb-4">
      <h3 class="text-lg font-semibold mb-2">Speaker Names</h3>
      <div v-for="speaker in uniqueSpeakers" :key="speaker" class="mb-2">
        <label :for="speaker" class="mr-2">{{ speaker }}:</label>
        <input :id="speaker" v-model="speakerNames[speaker]" @change="updateSpeakerNames"
          class="border rounded px-2 py-1" />
      </div>
    </div>
    <div class="mb-4">
      <h3 class="text-lg font-semibold mb-2">Download Options</h3>
      <button @click="downloadJson" class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded mr-2">
        Download JSON
      </button>
      <button @click="downloadText('raw')"
        class="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded mr-2">
        Download Raw Text
      </button>
      <button @click="downloadText('timestamped')"
        class="bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-2 px-4 rounded">
        Download Text with Timestamps
      </button>
    </div>
    <div class="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
      <!-- Check if transcript.speakers exists and has length > 0 -->
      <div v-if="transcript.speakers && transcript.speakers.length > 0">
        <div v-for="(segment, index) in transcript.speakers" :key="index" class="mb-4">
          <p class="text-sm text-gray-500 mb-1">
            {{ formatTime(segment.timestamp[0]) }} - {{ formatTime(segment.timestamp[1]) }}
            <span class="font-semibold">{{ speakerNames[segment.speaker] || segment.speaker }}:</span>
          </p>
          <p class="text-lg">{{ segment.text }}</p>
        </div>
      </div>
      <!-- Fallback to transcript.chunks if no speaker data is available -->
      <div v-else>
        <div v-for="(chunk, index) in transcript.chunks" :key="index" class="mb-4">
          <p class="text-sm text-gray-500 mb-1">
            {{ formatTime(chunk.timestamp[0]) }} - {{ formatTime(chunk.timestamp[1]) }}
          </p>
          <p class="text-lg">{{ chunk.text }}</p>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="col-start-2 col-end-7 justify-center items-center">
    <span class='italic'>Pick a file to see the transcript</span>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import axios from 'axios';

const props = defineProps({
  transcript: {
    type: Object,
    required: true
  },
  filename: {
    type: String,
    required: true
  }
});


const speakerNames = ref({});

const uniqueSpeakers = computed(() => {
  if (!props.transcript) return [];
  return [...new Set(props.transcript.speakers.map(s => s.speaker))];
});

watch(() => props.transcript, (newTranscript) => {
  if (newTranscript) {
    speakerNames.value = Object.fromEntries(
      uniqueSpeakers.value.map(speaker => [speaker, speaker])
    );
  }
}, { immediate: true });

const baseFilename = computed(() => props.filename.split('.').slice(0, -1).join('.'))

const formatTime = (seconds) => {
  if (typeof seconds !== 'number' || isNaN(seconds)) {
    return '00:00.000';
  }
  const date = new Date(seconds * 1000);
  const minutes = date.getUTCMinutes();
  const secs = date.getUTCSeconds();
  // const millisecs = date.getUTCMilliseconds();
  return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

const updateSpeakerNames = async () => {
  if (!props.filename) {
    console.error('Transcript filename is not provided');
    alert('Unable to update speaker names: Transcript filename is missing.');
    return;
  }
  try {
    await axios.post('http://' + import.meta.env.VITE_APP_BACKEND_URL + '/update_speaker_names', {
      transcript_filename: baseFilename.value + '.json',
      speaker_names: speakerNames.value
    });
    // You might want to emit an event or update the parent component here
  } catch (error) {
    console.error('Error updating speaker names:', error);
    alert('Failed to update speaker names. Please try again.');
  }
};

const downloadJson = () => {
  const jsonString = JSON.stringify(props.transcript, null, 2);
  downloadFile(jsonString, baseFilename.value + '.json', 'application/json');
};

const downloadText = (type) => {
  let content = '';
  if (type === 'raw') {
    content = props.transcript.text;
  } else if (type === 'timestamped') {
    if (props.transcript.speakers.length > 0) {
      content = props.transcript.speakers.map(segment =>
        `${formatTime(segment.timestamp[0])} - ${formatTime(segment.timestamp[1])} ${speakerNames.value[segment.speaker] || segment.speaker}: ${segment.text}`
      ).join('\n');
    } else {
      content = props.transcript.chunks.map(segment =>
        `${formatTime(segment.timestamp[0])} - ${formatTime(segment.timestamp[1])}: ${segment.text}`
      ).join('\n');
    }
  }
  downloadFile(content, `${baseFilename.value}_${type}.txt`, 'text/plain');
};

const downloadFile = (content, fileName, contentType) => {
  const a = document.createElement("a");
  const file = new Blob([content], { type: contentType });
  a.href = URL.createObjectURL(file);
  a.download = fileName;
  a.click();
  URL.revokeObjectURL(a.href);
};
</script>
