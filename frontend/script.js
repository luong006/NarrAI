const API_URL = "https://narrai-c1oc.onrender.com/api";

let globalData = {
    initialPrompt: "",
    chatHistory: [],
    refinedPrompt: "",
    selectedLength: "medium"
};

// UI Navigation
function showPhase(phaseNumber) {
    document.querySelectorAll('.phase').forEach(el => el.classList.remove('active'));
    document.getElementById(`phase${phaseNumber}`).classList.add('active');
}

// =================== PHASE 1 & 2: SETUP & INTERVIEW ===================
async function generateQuestions() {
    let prompt = document.getElementById('initialPrompt').value.trim();
    const genres = Array.from(selectedTags).join(", ");
    const themes = Array.from(selectedThemes).join(", ");
    
    let combinedPrompt = prompt;
    if (genres) combinedPrompt = `[Thể loại: ${genres}] ${combinedPrompt}`;
    if (themes) combinedPrompt = `[Chủ đề: ${themes}] ${combinedPrompt}`;

    if (!combinedPrompt) {
        alert("Vui lòng nhập ý tưởng hoặc chọn thể loại!");
        return;
    }

    globalData.initialPrompt = combinedPrompt;
    globalData.chatHistory = [{"role": "user", "content": combinedPrompt}];
    
    showPhase(2);
    const chatBox = document.getElementById('chatBox');
    chatBox.innerHTML = `
        <div class="chat-message chat-user">${combinedPrompt}</div>
        <div class="chat-message chat-ai" id="chatLoading">Đang phân tích...</div>
    `;

    try {
        const response = await fetch(`${API_URL}/chat-interview`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_history: globalData.chatHistory })
        });
        const data = await response.json();
        
        document.getElementById('chatLoading').remove();
        
        if (data.status === 'success') {
            globalData.chatHistory.push({"role": "assistant", "content": data.message});
            chatBox.innerHTML += `<div class="chat-message chat-ai">${formatAIResponse(data.message)}</div>`;
            
            if (data.is_ready) {
                forceRefinePrompt();
            }
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        document.getElementById('chatLoading').textContent = "Lỗi kết nối. Vui lòng thử lại.";
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const msg = input.value.trim();
    if(!msg) return;
    
    input.value = '';
    const chatBox = document.getElementById('chatBox');
    
    globalData.chatHistory.push({"role": "user", "content": msg});
    chatBox.innerHTML += `<div class="chat-message chat-user">${msg}</div>`;
    chatBox.innerHTML += `<div class="chat-message chat-ai" id="chatLoading">Đang suy nghĩ...</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const response = await fetch(`${API_URL}/chat-interview`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_history: globalData.chatHistory })
        });
        const data = await response.json();
        
        document.getElementById('chatLoading').remove();
        
        if (data.status === 'success') {
            globalData.chatHistory.push({"role": "assistant", "content": data.message});
            chatBox.innerHTML += `<div class="chat-message chat-ai">${formatAIResponse(data.message)}</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
            
            if (data.is_ready) {
                forceRefinePrompt();
            }
        }
    } catch (error) {
        document.getElementById('chatLoading').textContent = "Lỗi kết nối.";
    }
}

function formatAIResponse(text) {
    return text.replace(/\n/g, '<br>');
}

async function forceRefinePrompt() {
    const chatBox = document.getElementById('chatBox');
    chatBox.innerHTML += `<div class="chat-message chat-ai" style="color:#d97706">Đang chốt dàn ý và tổng hợp thông tin...</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const response = await fetch(`${API_URL}/refine-prompt`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_history: globalData.chatHistory })
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            globalData.refinedPrompt = data.refined_prompt;
            showPhase(3);
        }
    } catch (error) {
        alert("Lỗi chốt dàn ý.");
    }
}

// =================== PHASE 3: GENERATE & EDITOR WORKSPACE ===================
async function generateStory() {
    globalData.selectedLength = document.querySelector('input[name="length"]:checked').value;
    
    // Switch UI to Editor mode
    document.getElementById('setupView').style.display = 'none';
    document.getElementById('editorView').style.display = 'block';
    
    const output = document.getElementById('storyOutput');
    output.innerHTML = '<i>Đang khởi tạo bản thảo...</i><br><br>';
    
    try {
        const response = await fetch(`${API_URL}/generate-story`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                refined_prompt: globalData.refinedPrompt,
                story_length: globalData.selectedLength
            })
        });
        
        if (!response.ok) throw new Error(`Lỗi server`);
        
        output.innerHTML = '';
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let fullStory = "";
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            fullStory += chunk;
            
            const formattedStory = fullStory
                .split('\n')
                .filter(line => line.trim())
                .map(line => `<p>${line}</p>`)
                .join('');
            
            output.innerHTML = formattedStory;
            updateWordCount();
        }
    } catch (error) {
        output.innerHTML += `<p style="color: red;">Lỗi: ${error.message}</p>`;
    }
}

function updateWordCount() {
    const text = document.getElementById('storyOutput').innerText;
    const count = text.trim().split(/\s+/).filter(w => w.length > 0).length;
    document.getElementById('wordCount').textContent = `${count} từ`;
}

// =================== INTERACTIVE EDITING ===================
let currentSelectionRange = null;

// Track selection
document.addEventListener('selectionchange', () => {
    const selection = window.getSelection();
    const toolbar = document.getElementById('floatingToolbar');
    const editor = document.getElementById('storyOutput');
    
    // Check if selection is inside editor and not empty
    if (!selection.isCollapsed && editor.contains(selection.anchorNode)) {
        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();
        
        // Show toolbar above selection
        toolbar.style.display = 'flex';
        toolbar.style.top = `${rect.top + window.scrollY - 40}px`;
        toolbar.style.left = `${rect.left + (rect.width/2) - (toolbar.offsetWidth/2)}px`;
        
        currentSelectionRange = range;
    } else {
        // Hide if click away or empty
        toolbar.style.display = 'none';
    }
});

function openAIChatForSelection() {
    document.getElementById('floatingToolbar').style.display = 'none';
    const selectedText = currentSelectionRange.toString();
    
    document.getElementById('aiWelcomeMsg').style.display = 'none';
    document.getElementById('aiResultBox').style.display = 'none';
    
    const box = document.getElementById('aiSelectionBox');
    box.style.display = 'block';
    document.getElementById('aiSelectionText').textContent = selectedText;
    document.getElementById('aiCustomInstruction').value = '';
    document.getElementById('aiCustomInstruction').focus();
}

function interactiveEdit(instruction) {
    document.getElementById('floatingToolbar').style.display = 'none';
    const selectedText = currentSelectionRange.toString();
    
    document.getElementById('aiWelcomeMsg').style.display = 'none';
    document.getElementById('aiSelectionBox').style.display = 'block';
    document.getElementById('aiSelectionText').textContent = selectedText;
    document.getElementById('aiCustomInstruction').value = instruction;
    
    submitCustomEdit();
}

async function submitCustomEdit() {
    const originalText = document.getElementById('aiSelectionText').textContent;
    const instruction = document.getElementById('aiCustomInstruction').value;
    
    if(!instruction.trim()) {
        alert("Vui lòng nhập yêu cầu!");
        return;
    }
    
    document.getElementById('aiSelectionBox').style.display = 'none';
    document.getElementById('aiLoading').style.display = 'block';
    
    try {
        const response = await fetch(`${API_URL}/edit-text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                original_text: originalText,
                instruction: instruction
            })
        });
        const data = await response.json();
        
        document.getElementById('aiLoading').style.display = 'none';
        
        if(data.status === 'success') {
            document.getElementById('aiResultBox').style.display = 'block';
            document.getElementById('aiNewText').innerHTML = data.revised_text.replace(/\n/g, '<br>');
        }
    } catch(e) {
        document.getElementById('aiLoading').style.display = 'none';
        alert("Lỗi kết nối AI!");
        document.getElementById('aiSelectionBox').style.display = 'block';
    }
}

function acceptEdit() {
    const newText = document.getElementById('aiNewText').innerText; // Use innerText to strip HTML for insertion
    if (currentSelectionRange) {
        // Create text node and replace
        currentSelectionRange.deleteContents();
        currentSelectionRange.insertNode(document.createTextNode(newText));
        
        // Clean up UI
        document.getElementById('aiResultBox').style.display = 'none';
        document.getElementById('aiWelcomeMsg').style.display = 'block';
        updateWordCount();
    }
}

function rejectEdit() {
    document.getElementById('aiResultBox').style.display = 'none';
    document.getElementById('aiWelcomeMsg').style.display = 'block';
}


// =================== INIT & MISC ===================
let selectedTags = new Set();
let selectedThemes = new Set();
const allGenres = [
    "Isekai (Xuyên không)", "Harem", "Tổng tài", "Ngôn tình", 
    "Hệ thống", "Trùng sinh", "Nữ cường", "Đam mỹ", 
    "Hài hước", "Chữa lành", "Khoa học viễn tưởng", "Kinh dị",
    "Tiên hiệp", "Huyền huyễn", "Học đường", "Trinh thám"
];

function initGenres() {
    const genresContainer = document.getElementById('genresContainer');
    if (!genresContainer) return;
    genresContainer.innerHTML = '';
    
    allGenres.forEach(genre => {
        const tag = document.createElement('div');
        tag.className = 'trending-tag';
        tag.textContent = genre;
        tag.onclick = (e) => {
            e.preventDefault();
            tag.classList.toggle('selected-tag');
            if (selectedTags.has(genre)) selectedTags.delete(genre);
            else selectedTags.add(genre);
        };
        genresContainer.appendChild(tag);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initGenres();
    // fetchTrendingTopics() ... skipped for brevity
});

function downloadStory() {
    const storyText = document.getElementById('storyOutput').innerText;
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(storyText));
    element.setAttribute('download', 'ban-thao.txt');
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
}

// Modal History methods...
function openHistory() { document.getElementById('historyModal').style.display = 'block'; }
function closeHistory() { document.getElementById('historyModal').style.display = 'none'; }
window.onclick = function(event) { if (event.target == document.getElementById('historyModal')) closeHistory(); }
