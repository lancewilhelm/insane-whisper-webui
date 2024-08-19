<template>
  <div class="min-h-screen bg-gray-100">
    <Header />
    <main class="container mx-auto px-4 py-8">
      <div class="bg-white shadow-md rounded-lg p-6">
        <FileUploader @file-uploaded="handleFileUploaded" />
      </div>
      <div class="bg-white shadow-md rounded-lg p-6 mt-8">
        <h2 class="text-2xl font-semibold mb-4">Files & Transcripts</h2>
        <div class="grid grid-cols-6 gap-8">
          <FileList @show-transcript="showTranscript" />
          <TranscriptViewer :transcript="currentTranscript" :filename="currentTranscriptFilename" />
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import Header from './components/Header.vue';
import FileUploader from './components/FileUploader.vue';
import FileList from './components/FileList.vue';
import TranscriptViewer from './components/TranscriptViewer.vue';

const currentTranscript = ref(null);
const currentTranscriptFilename = ref('');

const handleFileUploaded = (transcriptData) => {
  currentTranscript.value = transcriptData;
  currentTranscriptFilename.value = ''; // You might want to set this based on the uploaded file
};

const showTranscript = ({ transcript, filename }) => {
  currentTranscript.value = transcript;
  currentTranscriptFilename.value = filename;
};
</script>
