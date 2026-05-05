document.querySelectorAll("[data-preview-input]").forEach((input) => {
    input.addEventListener("change", (event) => {
        const key = event.currentTarget.dataset.previewInput;
        const preview = document.querySelector(`[data-preview-target="${key}"]`);
        const fileName = document.querySelector(`[data-file-name="${key}"]`);
        const [file] = event.currentTarget.files || [];

        if (!file) {
            return;
        }

        if (fileName) {
            fileName.textContent = `Выбран файл: ${file.name}`;
        }

        if (!preview) {
            return;
        }

        const reader = new FileReader();
        reader.onload = ({ target }) => {
            preview.src = target.result;
        };
        reader.readAsDataURL(file);
    });
});

const getCsrfToken = (form) => {
    const input = form.querySelector("[name=csrfmiddlewaretoken]");
    return input ? input.value : "";
};

const appendChatMessage = (container, role, author, text) => {
    const message = document.createElement("article");
    message.className = `chat-message ${role}`;
    const label = document.createElement("span");
    label.textContent = author;
    const body = document.createElement("p");
    body.textContent = text;
    message.append(label, body);
    container.append(message);
    container.scrollTop = container.scrollHeight;
};

const mergeAudioChunks = (chunks, length) => {
    const result = new Float32Array(length);
    let offset = 0;
    chunks.forEach((chunk) => {
        result.set(chunk, offset);
        offset += chunk.length;
    });
    return result;
};

const writeString = (view, offset, value) => {
    for (let index = 0; index < value.length; index += 1) {
        view.setUint8(offset + index, value.charCodeAt(index));
    }
};

const floatTo16BitPcm = (view, offset, input) => {
    for (let index = 0; index < input.length; index += 1, offset += 2) {
        const sample = Math.max(-1, Math.min(1, input[index]));
        view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
    }
};

const encodeWav = (samples, sampleRate) => {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);
    writeString(view, 0, "RIFF");
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(view, 8, "WAVE");
    writeString(view, 12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(view, 36, "data");
    view.setUint32(40, samples.length * 2, true);
    floatTo16BitPcm(view, 44, samples);
    return new Blob([view], { type: "audio/wav" });
};

document.querySelectorAll("[data-chat-form]").forEach((form) => {
    const textarea = form.querySelector("textarea[name=message]");
    const status = document.querySelector("[data-chat-status]");
    const messages = document.querySelector("[data-chat-messages]");
    const quickReplies = document.querySelector("[data-quick-replies]");
    const voiceButton = form.querySelector("[data-voice-button]");
    const csrfToken = getCsrfToken(form);

    const setStatus = (text) => {
        if (status) {
            status.textContent = text;
        }
    };

    const hideQuickReplies = () => {
        if (!quickReplies || quickReplies.hidden) {
            return;
        }
        quickReplies.classList.add("is-hidden");
        window.setTimeout(() => {
            quickReplies.hidden = true;
        }, 220);
    };

    const sendChatMessage = async (source = "text", explicitMessage = "") => {
        const message = (explicitMessage || textarea.value).trim();
        if (!message) {
            return;
        }

        hideQuickReplies();
        appendChatMessage(messages, "user", "Вы", message);
        textarea.value = "";
        setStatus("Travel X AI думает...");

        try {
            const response = await fetch(form.dataset.messageUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken,
                },
                body: JSON.stringify({ message, source }),
            });
            const payload = await response.json();
            if (!response.ok) {
                throw new Error(payload.error || "Ошибка AI-сервиса.");
            }
            appendChatMessage(messages, "assistant", "Travel X AI", payload.answer);
            setStatus("");
        } catch (error) {
            appendChatMessage(messages, "assistant", "Travel X AI", error.message);
            setStatus("");
        }
    };

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        sendChatMessage("text");
    });

    document.querySelectorAll("[data-quick-reply]").forEach((button) => {
        button.addEventListener("click", () => {
            const question = button.dataset.quickReply || button.textContent;
            textarea.value = question;
            sendChatMessage("quick_reply", question);
        });
    });

    if (!voiceButton || !navigator.mediaDevices) {
        return;
    }

    let audioContext = null;
    let processor = null;
    let source = null;
    let stream = null;
    let chunks = [];
    let recordingLength = 0;

    voiceButton.addEventListener("click", async () => {
        if (stream) {
            processor.disconnect();
            source.disconnect();
            stream.getTracks().forEach((track) => track.stop());
            const samples = mergeAudioChunks(chunks, recordingLength);
            const wavBlob = encodeWav(samples, audioContext.sampleRate);
            await audioContext.close();

            stream = null;
            audioContext = null;
            voiceButton.textContent = "Записать голос";
            setStatus("Распознаю голос...");

            const formData = new FormData();
            formData.append("audio", wavBlob, "voice.wav");
            formData.append("language", "ru-RU");

            try {
                const response = await fetch(form.dataset.transcribeUrl, {
                    method: "POST",
                    headers: { "X-CSRFToken": csrfToken },
                    body: formData,
                });
                const payload = await response.json();
                if (!response.ok) {
                    throw new Error(payload.error || "Не удалось распознать голос.");
                }
                textarea.value = payload.transcript;
                await sendChatMessage("voice");
            } catch (error) {
                setStatus(error.message);
            }
            return;
        }

        chunks = [];
        recordingLength = 0;
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioContext = new AudioContext();
        source = audioContext.createMediaStreamSource(stream);
        processor = audioContext.createScriptProcessor(4096, 1, 1);
        processor.onaudioprocess = (event) => {
            const channel = event.inputBuffer.getChannelData(0);
            chunks.push(new Float32Array(channel));
            recordingLength += channel.length;
        };
        source.connect(processor);
        processor.connect(audioContext.destination);
        voiceButton.textContent = "Остановить запись";
        setStatus("Идет запись...");
    });
});
