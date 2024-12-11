class VoiceAssistant {
    constructor() {
        this.socket = null;
        this.audioContext = null;
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.token = null;
        this.audioQueue = [];
        this.isRecording = false;
        this.processor = null;
        this.audioSource = null;
        this.isPlaying = false;
        this.mediaRecorder = null;
        this.audioChunks = [];

        this.startBtn.addEventListener('click', () => this.login());
        this.stopBtn.addEventListener('click', () => this.stopConversation());
    }

    async login() {
        const email = prompt("Please enter your email:");
        const password = prompt("Please enter your password:");
        try {
            const response = await fetch('https://api.themark.academy/backend/api/user/userLogin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (data.success) {
                this.token = data.data.token;
                this.startConversation();
            } else {
                console.error('Login failed:', data.message);
            }
        } catch (error) {
            console.error('Error during login:', error);
        }
    }

    async startConversation() {
        try {
            await this.setupAudioInput();
            this.connectWebSocket();
            this.startBtn.disabled = true;
            this.stopBtn.disabled = false;
            this.isRecording = true;
        } catch (error) {
            console.error('Error starting conversation:', error);
        }
    }

    stopConversation() {
        this.isRecording = false;
        if (this.mediaRecorder) {
            this.mediaRecorder.stop();
        }
        if (this.socket) {
            this.socket.close();
        }
        this.startBtn.disabled = false;
        this.stopBtn.disabled = true;
        this.audioQueue = [];
        this.isPlaying = false;
    }

    async setupAudioInput() {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
        const source = this.audioContext.createMediaStreamSource(stream);
        this.processor = this.audioContext.createScriptProcessor(16384, 1, 1);

        source.connect(this.processor);
        this.processor.connect(this.audioContext.destination);

        this.processor.onaudioprocess = (e) => {
            if (this.isRecording) {
                const inputData = e.inputBuffer.getChannelData(0);
                this.sendAudioData(inputData);
            }
        };
    }

    sendAudioData(audioData) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            const pcm16 = new Int16Array(audioData.length);
            for (let i = 0; i < audioData.length; i++) {
                pcm16[i] = audioData[i] * 32767;
            }
            const base64Audio = btoa(String.fromCharCode.apply(null, new Uint8Array(pcm16.buffer)));
            const message = JSON.stringify({
                type: "audio",
                payload: base64Audio
            });
            this.socket.send(message);
        }
    }

    connectWebSocket() {
        this.socket = new WebSocket('ws://localhost:8000/api/v1/voice-ai/media-stream');
        this.socket.onopen = () => {
            console.log('WebSocket connected');
            if (this.token) {
                this.socket.send(JSON.stringify({ token: this.token }));
            }
        };

        this.socket.onmessage = async (event) => {
            const data = JSON.parse(event.data);
            if (data.type === "audio") {
                const audioBuffer = this.base64ToArrayBuffer(data.payload);
                this.audioQueue.push(audioBuffer);
                if (!this.isPlaying) {
                    await this.playNextAudio();
                }
            } else if (data.type === "speech_started") {
                console.log("User started speaking!");
                this.audioQueue = [];
                if (this.audioSource) {
                    this.audioSource.stop();
                }
                this.isPlaying = false;
            }
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.socket.onclose = () => {
            console.log('WebSocket closed');
        };
    }

    base64ToArrayBuffer(base64) {
        const binaryString = atob(base64);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        return bytes.buffer;
    }

    async playNextAudio() {
        while (this.audioQueue.length > 0) {
            this.isPlaying = true;
            const arrayBuffer = this.audioQueue.shift();
            const audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });

            const numberOfChannels = 1;
            const length = arrayBuffer.byteLength / 2;
            const sampleRate = 24000;
            const audioBuffer = audioContext.createBuffer(numberOfChannels, length, sampleRate);
            
            const channelData = audioBuffer.getChannelData(0);
            const view = new Int16Array(arrayBuffer);
            for (let i = 0; i < length; i++) {
                channelData[i] = view[i] / 32768.0;
            }
            
            this.audioSource = audioContext.createBufferSource();
            this.audioSource.buffer = audioBuffer;
            this.audioSource.connect(audioContext.destination);
            
            await new Promise(resolve => {
                this.audioSource.onended = resolve;
                this.audioSource.start();
            });
        }
        this.isPlaying = false;
    }
}

const assistant = new VoiceAssistant();
