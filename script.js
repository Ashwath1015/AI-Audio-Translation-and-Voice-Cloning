document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;

    // Upload Elements
    const videoUpload = document.getElementById('video-upload');
    const uploadPlaceholder = document.getElementById('upload-placeholder');
    const filePreviewContainer = document.getElementById('file-preview-container');
    const localPreview = document.getElementById('local-preview');
    const fileNameDisplay = document.getElementById('file-name-display');
    const fileSizeDisplay = document.getElementById('file-size-display');
    const removeFileBtn = document.getElementById('remove-file');

    // Link Upload
    // (Elements removed from HTML, but kept as null to avoid crashes)
    const urlUpload = null;
    const urlSubmit = null;

    // Options Elements
    const sourceLang = document.getElementById('source-lang');
    const targetLang = document.getElementById('language-select');
    const consentCheckbox = document.getElementById('consent-checkbox');

    // General Controls
    const translateBtn = document.getElementById('translate-btn');
    const errorMessage = document.getElementById('error-message');
    const processingSection = document.getElementById('processing-section');
    const progressBar = document.getElementById('progress-bar');
    const statusText = document.getElementById('status-text');
    const resultSection = document.getElementById('result-section');
    const finalLangDisplay = document.getElementById('final-lang');
    const resetBtn = document.getElementById('reset-btn');
    const cancelBtn = document.getElementById('cancel-btn');
    const dropZone = document.getElementById('drop-zone');

    // Result-specific elements
    const resultOriginalVideo = document.getElementById('result-original-video');
    const resultTranslatedVideo = document.getElementById('result-translated-video');
    const originalTranscriptBox = document.getElementById('original-transcript');
    const translatedTranscriptBox = document.getElementById('translated-transcript');

    // Backend API Configuration
    const API_BASE_URL = 'http://localhost:8000';

    // --- Theme Logic ---
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        body.classList.add('dark-mode');
        themeToggle.innerHTML = '<span class="mode-icon">☀️</span>';
    }

    themeToggle.addEventListener('click', () => {
        body.classList.toggle('dark-mode');
        const isDark = body.classList.contains('dark-mode');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        themeToggle.innerHTML = isDark ? '<span class="mode-icon">☀️</span>' : '<span class="mode-icon">🌙</span>';
    });

    // --- Info Modal Logic ---
    const infoModal = document.getElementById('info-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    const closeModalBtn = document.getElementById('close-modal');

    const pageContent = {
        'pricing': {
            title: 'Pricing',
            content: '<p>VoiceDub AI is built on a <strong>local-first AI pipeline</strong>. This means there are no monthly subscriptions, no expensive API credits, and no hidden fees.</p><p>Since the processing happens on your own hardware, the service is <strong>100% free forever</strong>. You only pay for the electricity your computer uses!</p>'
        },
        'features': {
            title: 'Features',
            content: '<p>Our advanced pipeline consists of several AI-driven stages:</p><ul><li><strong>Vocal Analysis:</strong> Captures your unique timbre and speech patterns.</li><li><strong>Whisper Transcription:</strong> High-accuracy local transcription.</li><li><strong>Argos Translation:</strong> Offline, privacy-preserving translation.</li><li><strong>Voice Synthesis:</strong> Native-sounding speech generation.</li><li><strong>FFmpeg Merge:</strong> Seamless audio-video synchronization.</li></ul>'
        },
        'api': {
            title: 'Developer API',
            content: '<p>VoiceDub AI is powered by a high-performance <strong>FastAPI backend</strong>. The API allows for asynchronous job submission and status polling.</p><p>Key endpoints include <code>/upload</code> for starting jobs and <code>/status/{job_id}</code> for tracking progress. The backend is designed to be extensible, allowing for the integration of new AI models easily.</p>'
        },
        'about': {
            title: 'About VoiceDub AI',
            content: '<p>VoiceDub AI is a project dedicated to breaking language barriers using the power of local AI. Our vision is to democratize high-quality video localization, making it accessible to everyone without relying on centralized cloud providers.</p><p>By moving the AI to the edge, we ensure that creators maintain full ownership of their content and biometric data.</p>'
        },
        'privacy': {
            title: 'Privacy Policy',
            content: '<p>Your privacy is our primary architectural constraint. VoiceDub AI follows a <strong>Zero-Cloud Policy</strong>:</p><ul><li><strong>Local Processing:</strong> Your videos never leave your machine.</li><li><strong>No Data Mining:</strong> We do not collect, store, or analyze your voice data.</li><li><strong>Offline First:</strong> Most of the pipeline operates without an internet connection.</li></ul><p>You have total control over your data.</p>'
        },
        'terms': {
            title: 'Terms of Service',
            content: '<p>By using VoiceDub AI, you agree to the following:</p><ul><li><strong>Ownership:</strong> You must own the rights to the video and voice you are cloning.</li><li><strong>Ethical Use:</strong> This tool must not be used to create deepfakes for deceptive or malicious purposes.</li><li><strong>Demo Status:</strong> This is a demonstration project; we are not responsible for any hardware stress caused by local AI processing.</li></ul>'
        },
        'help': {
            title: 'Help Center',
            content: '<p>Getting started with VoiceDub AI is simple:</p><ol><li>Upload a video (MP4, MOV, or WebM).</li><li>Select the original language (or use Auto-detect).</li><li>Choose your target translation language.</li><li>Confirm ownership and click "Start Translation".</li></ol><p>If the process seems slow, ensure your computer has enough free RAM and that FFmpeg is correctly installed in your system PATH.</p>'
        },
        'contact': {
            title: 'Contact Us',
            content: '<p>We are always looking for contributors and feedback!</p><p><strong>GitHub:</strong> Visit our repository at <a href="https://github.com/Ashwath1015" target="_blank" style="color: var(--primary);">github.com/Ashwath1015</strong> to report bugs or submit pull requests.</p><p><strong>Email:</strong> <a href="mailto:easwaranashwath97@gmail.com" style="color: var(--primary);">easwaranashwath97@gmail.com</strong></p>'
        },
        'status': {
            title: 'System Status',
            content: '<p>Since VoiceDub AI runs locally, the "system status" depends on your own machine.</p><p><strong>Backend:</strong> Ensure the FastAPI server is running on <code>localhost:8000</code>.</p><p><strong>Database:</strong> MongoDB must be active on <code>localhost:27017</code>.</p><p><strong>Engine:</strong> FFmpeg must be accessible via the command line.</p>'
        }
    };

    document.querySelectorAll('.footer-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.getAttribute('data-page');
            const data = pageContent[page];

            if (data) {
                modalTitle.textContent = data.title;
                modalBody.innerHTML = data.content;
                infoModal.classList.remove('hidden');
            }
        });
    });

    const closeModal = () => {
        infoModal.classList.add('hidden');
    };

    closeModalBtn.addEventListener('click', closeModal);

    // Close when clicking the overlay
    infoModal.addEventListener('click', (e) => {
        if (e.target === infoModal.querySelector('.modal-overlay')) {
            closeModal();
        }
    });

    // --- Validation State ---
    let isFileUploaded = false;
    let isLinkUploaded = false;

    function updateTranslateButtonState() {
        const hasSource = isFileUploaded || isLinkUploaded;
        const hasConsent = consentCheckbox.checked;
        translateBtn.disabled = !(hasSource && hasConsent);
    }

    // --- File Validation & Handling ---
    const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500 MB
    const ALLOWED_TYPES = ['video/mp4', 'video/quicktime', 'video/webm'];

    function showError(msg) {
        errorMessage.textContent = msg;
        errorMessage.classList.remove('hidden');
        setTimeout(() => errorMessage.classList.add('hidden'), 4000);
    }

    function handleFile(file) {
        if (!file) return;
        if (!ALLOWED_TYPES.includes(file.type)) {
            showError("Unsupported file type. Please use MP4, MOV or WebM.");
            return;
        }
        if (file.size > MAX_FILE_SIZE) {
            showError("File is too large. Maximum size is 500 MB.");
            return;
        }

        errorMessage.classList.add('hidden');
        uploadPlaceholder.classList.add('hidden');
        filePreviewContainer.classList.remove('hidden');
        fileNameDisplay.textContent = file.name;
        fileSizeDisplay.textContent = (file.size / (1024 * 1024)).toFixed(2) + " MB";
        const fileURL = URL.createObjectURL(file);
        localPreview.src = fileURL;
        localPreview.load();
        isFileUploaded = true;
        isLinkUploaded = false;
        updateTranslateButtonState();
    }

    videoUpload.addEventListener('change', (e) => {
        const file = e.target.files[0];
        handleFile(file);
    });

    removeFileBtn.addEventListener('click', (e) => {
        e.preventDefault();
        videoUpload.value = '';
        uploadPlaceholder.classList.remove('hidden');
        filePreviewContainer.classList.add('hidden');
        localPreview.src = '';
        isFileUploaded = false;
        updateTranslateButtonState();
    });

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFile(files[0]);
            videoUpload.files = files;
        }
    });

    urlSubmit?.addEventListener('click', () => {
        const url = urlUpload?.value?.trim();
        if (!url) {
            showError("Please enter a valid URL.");
            return;
        }
        urlUpload.value = '';
        urlUpload.placeholder = "Link added successfully!";
        isLinkUploaded = true;
        isFileUploaded = false;
        updateTranslateButtonState();
        urlUpload.style.borderColor = 'var(--primary)';
        setTimeout(() => {
            urlUpload.style.borderColor = 'var(--card-border)';
            urlUpload.placeholder = "YouTube, Vimeo or direct URL...";
        }, 3000);
    });

    consentCheckbox.addEventListener('change', updateTranslateButtonState);

    // --- Real Backend Translation Logic ---
    let pollingInterval = null;

    async function startTranslation() {
        if (!isFileUploaded) {
            showError("Please upload a video first.");
            return;
        }

        document.querySelector('.upload-grid').classList.add('hidden');
        processingSection.classList.remove('hidden');
        translateBtn.disabled = true;

        const formData = new FormData();
        formData.append('file', videoUpload.files[0]);
        formData.append('source_lang', sourceLang.value);
        formData.append('target_lang', targetLang.value);
        formData.append('voice_style', 'original');
        formData.append('voice_cloning', true);
        formData.append('add_subtitles', false);

        // DEBUG LOG: This will show up in the Browser's Inspect -> Console (F12)
        console.log("Sending to backend:", {
            source: sourceLang.value,
            target: targetLang.value,
            voice: 'original'
        });

        try {
            const response = await fetch(`${API_BASE_URL}/upload`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) throw new Error('Upload failed');

            const data = await response.json();
            const jobId = data.job_id;

            pollStatus(jobId);

        } catch (error) {
            showError("Server error: " + error.message);
            cancelTranslation();
        }
    }

    async function pollStatus(jobId) {
        pollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/status/${jobId}`);
                if (!response.ok) throw new Error('Status check failed');

                const data = await response.json();

                progressBar.style.width = `${data.progress}%`;
                statusText.textContent = data.status;

                if (data.status === 'completed') {
                    clearInterval(pollingInterval);
                    showResult(data.result_url, data.original_text, data.translated_text);
                } else if (data.status.startsWith('Error')) {
                    clearInterval(pollingInterval);
                    showError(data.status);
                    cancelTranslation();
                }
            } catch (error) {
                console.error("Polling error:", error);
            }
        }, 2000);
    }

    function showResult(resultUrl, originalText, translatedText) {
        processingSection.classList.add('hidden');
        resultSection.classList.remove('hidden');

        const langName = targetLang.options[targetLang.selectedIndex].text.split(' ')[0];
        finalLangDisplay.textContent = langName;

        const fileURL = URL.createObjectURL(videoUpload.files[0]);
        resultOriginalVideo.src = fileURL;

        // Use a direct download link or the API URL
        const translatedVideoUrl = `${API_BASE_URL}${resultUrl}`;
        resultTranslatedVideo.src = translatedVideoUrl;

        // Fix: Explicitly call load() and play() if the browser blocks autoplay
        resultTranslatedVideo.load();

        // Update transcript with REAL text from the backend
        if (originalText && translatedText) {
            displayRealTranscript(originalText, translatedText);
        } else {
            generateFakeTranscript();
        }

        // Fix: Implement the Download Dubbed Video button functionality
        const downloadBtn = resultSection.querySelector('.btn-primary');
        if (downloadBtn) {
            downloadBtn.onclick = () => {
                window.open(translatedVideoUrl, '_blank');
            };
        }
    }

    function displayRealTranscript(original, translated) {
        originalTranscriptBox.innerHTML = '';
        translatedTranscriptBox.innerHTML = '';

        const origLines = original.split('. ');
        const transLines = translated.split('. ');

        const maxLines = Math.max(origLines.length, transLines.length);

        for (let i = 0; i < maxLines; i++) {
            const timestamp = `00:0${i + 1}`;

            const origLine = document.createElement('div');
            origLine.className = 'transcript-line';
            origLine.innerHTML = `<span>${timestamp}</span> ${origLines[i] || ''}`;
            originalTranscriptBox.appendChild(origLine);

            const transLine = document.createElement('div');
            transLine.className = 'transcript-line';
            transLine.innerHTML = `<span>${timestamp}</span> ${transLines[i] || ''}`;
            translatedTranscriptBox.appendChild(transLine);
        }
    }

    function generateFakeTranscript() {
        const data = [
            { original: "Hello everyone, welcome to our new AI showcase!", translated: "¡Hola a todos, bienvenidos a nuestra nueva exhibición de IA!" },
            { original: "Imagine speaking every language in the world naturally.", translated: " la base de un cambio en la comunicación global." }
        ];
        originalTranscriptBox.innerHTML = '';
        translatedTranscriptBox.innerHTML = '';
        data.forEach((item, index) => {
            const timestamp = `00:0${index + 1}`;
            const origLine = document.createElement('div');
            origLine.className = 'transcript-line';
            origLine.innerHTML = `<span>${timestamp}</span>${item.original}`;
            originalTranscriptBox.appendChild(origLine);
            const transLine = document.createElement('div');
            transLine.className = 'transcript-line';
            transLine.innerHTML = `<span>${timestamp}</span>${item.translated}`;
            translatedTranscriptBox.appendChild(transLine);
        });
    }

    function cancelTranslation() {
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }
        processingSection.classList.add('hidden');
        document.querySelector('.upload-grid').classList.remove('hidden');
        translateBtn.disabled = false;
        progressBar.style.width = '0%';
    }

    translateBtn.addEventListener('click', startTranslation);
    cancelBtn.addEventListener('click', cancelTranslation);

    resetBtn.addEventListener('click', () => {
        resultSection.classList.add('hidden');
        processingSection.classList.add('hidden');
        document.querySelector('.upload-grid').classList.add('hidden');
        videoUpload.value = '';
        if (urlUpload) urlUpload.value = '';
        uploadPlaceholder.classList.remove('hidden');
        filePreviewContainer.classList.add('hidden');
        isFileUploaded = false;
        isLinkUploaded = false;
        consentCheckbox.checked = false;
        updateTranslateButtonState();
        document.querySelector('.upload-grid').classList.remove('hidden');
    });
});
