class VoiceAssistant {
    constructor() {
        this.socket = null;
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.audioQueue = [];
        this.isPlaying = false;

        this.startBtn.addEventListener('click', () => this.startConversation());
        this.stopBtn.addEventListener('click', () => this.stopConversation());
    }

    async startConversation() {
        try {
            await this.setupAudioInput();
            this.connectWebSocket();
            this.startBtn.disabled = true;
            this.stopBtn.disabled = false;
        } catch (error) {
            console.error('Error starting conversation:', error);
        }
    }

    stopConversation() {
        if (this.audioContext) {
            this.audioContext.close();
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
        this.audioContext = new AudioContext({ sampleRate: 24000 });
        const source = this.audioContext.createMediaStreamSource(stream);
        const processor = this.audioContext.createScriptProcessor(1024, 1, 1);

        source.connect(processor);
        processor.connect(this.audioContext.destination);

        processor.onaudioprocess = (e) => {
            const inputData = e.inputBuffer.getChannelData(0);
            const pcmData = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
                pcmData[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7FFF;
            }
            this.sendAudioData(pcmData.buffer);
        };
    }

    sendAudioData(buffer) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        const base64Audio = btoa(String.fromCharCode.apply(null, new Uint8Array(buffer)));
        const message = JSON.stringify({
            payload: base64Audio
        });
        this.socket.send(message);
    }
}

    connectWebSocket() {
        this.socket = new WebSocket('ws://localhost:5050/media-stream');
        this.socket.onopen = () => {
            console.log('WebSocket connected');
        };

        this.socket.onmessage = async (event) => {
        const data = JSON.parse(event.data);
        if (data.payload) {
            const audioBuffer = this.base64ToArrayBuffer(data.payload);
                this.audioQueue.push(audioBuffer);
                if (!this.isPlaying) {
                    this.playNextAudio();
            }
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
        if (this.audioQueue.length === 0) {
            this.isPlaying = false;
            return;
        }

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
    
    const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
    source.connect(audioContext.destination);
        source.onended = () => {
            this.playNextAudio();
        };
        source.start();
    }
}

const assistant = new VoiceAssistant();
