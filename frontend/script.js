const API_URL = "http://localhost:8000/api";

let globalData = {
    initialPrompt: "",
    userAnswers: [],
    refinedPrompt: "",
    selectedLength: "medium"
};
let chatHistory = [];

// Show specific phase
function showPhase(phaseNum) {
    document.querySelectorAll('.phase').forEach(p => p.classList.remove('active'));
    document.getElementById(`phase${phaseNum}`).classList.add('active');
    window.scrollTo(0, 0);
}

// Phase 1: Generate Questions
async function generateQuestions() {
    let prompt = document.getElementById('initialPrompt').value.trim();
    
    let combinedStr = "";
    if (selectedTags.size > 0) {
        combinedStr += `\n- Thể loại: ${Array.from(selectedTags).join(", ")}`;
    }
    if (selectedThemes.size > 0) {
        combinedStr += `\n- Chủ đề kết hợp: ${Array.from(selectedThemes).join(", ")}`;
    }
    
    if (combinedStr) {
        if (prompt) {
            prompt += `\n\nYêu cầu bổ sung:${combinedStr}`;
        } else {
            prompt = `Hãy viết một câu chuyện dựa trên các yêu cầu sau:${combinedStr}`;
        }
    }
    
    if (!prompt) {
        alert('Vui lòng nhập ý tưởng truyện hoặc chọn ít nhất 1 thể loại/chủ đề!');
        return;
    }
    
    globalData.initialPrompt = prompt;
    
    // Initialize chat history with the initial prompt as a system/user context
    chatHistory = [
        { role: 'user', content: `Ý tưởng cốt truyện của tôi: ${prompt}` }
    ];
    
    showPhase(2);
    const chatBox = document.getElementById('chatBox');
    chatBox.innerHTML = '<div class="chat-message chat-ai">Đang phân tích ý tưởng của bạn...</div>';
    
    try {
        const response = await fetch(`${API_URL}/chat-interview`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_history: chatHistory })
        });
        
        const data = await response.json();
        chatBox.innerHTML = ''; // Clear loading
        
        if (data.status === 'success') {
            chatHistory.push({ role: 'assistant', content: data.message });
            appendChatMessage('ai', data.message);
        } else {
            throw new Error(data.message || 'Lỗi khởi tạo chat');
        }
    } catch (error) {
        chatBox.innerHTML = `<p style="color: red;">Lỗi: ${error.message}</p>`;
    }
}

function appendChatMessage(sender, message) {
    const chatBox = document.getElementById('chatBox');
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message chat-${sender}`;
    // Format newlines
    msgDiv.innerHTML = message.replace(/\n/g, '<br>');
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const userText = input.value.trim();
    if (!userText) return;
    
    appendChatMessage('user', userText);
    chatHistory.push({ role: 'user', content: userText });
    input.value = '';
    
    appendChatMessage('ai', '...');
    const chatBox = document.getElementById('chatBox');
    const loadingBubble = chatBox.lastElementChild;
    
    try {
        const response = await fetch(`${API_URL}/chat-interview`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_history: chatHistory })
        });
        
        const data = await response.json();
        chatBox.removeChild(loadingBubble);
        
        if (data.status === 'success') {
            chatHistory.push({ role: 'assistant', content: data.message });
            appendChatMessage('ai', data.message);
            
            if (data.is_ready) {
                // The AI signaled it is ready, auto-advance after 2 seconds
                setTimeout(() => forceRefinePrompt(), 2000);
            }
        } else {
            throw new Error(data.message || 'Lỗi chat');
        }
    } catch (error) {
        chatBox.removeChild(loadingBubble);
        appendChatMessage('ai', `Lỗi: ${error.message}`);
    }
}

// Allow Enter key to send message
document.getElementById('chatInput')?.addEventListener('keypress', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
    }
});

// Phase 2: Refine Prompt (Triggered by button or AI ready)
async function forceRefinePrompt() {
    if (chatHistory.length < 2) {
        alert('Vui lòng đợi AI tải câu hỏi đầu tiên.');
        return;
    }
    
    showPhase(3);
    const statusDiv = document.createElement('div');
    statusDiv.className = 'loading';
    statusDiv.innerHTML = '<div class="spinner"></div><p>Đang tổng hợp cốt truyện chi tiết...</p>';
    document.querySelector('main').insertBefore(statusDiv, document.querySelector('#phase3'));
    
    try {
        const response = await fetch(`${API_URL}/refine-prompt`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_history: chatHistory })
        });
        
        const data = await response.json();
        statusDiv.remove();
        
        if (data.status === 'success') {
            globalData.refinedPrompt = data.refined_prompt;
        } else {
            throw new Error(data.message || 'Lỗi cô đọng ý tưởng');
        }
    } catch (error) {
        statusDiv.innerHTML = `<p style="color: red;">Lỗi: ${error.message}</p>`;
    }
}

// Phase 3: Generate Story
async function generateStory() {
    globalData.selectedLength = document.querySelector('input[name="length"]:checked').value;
    
    showPhase(4);
    const output = document.getElementById('storyOutput');
    output.innerHTML = '';
    const wordCountDisplay = document.getElementById('wordCount');
    wordCountDisplay.textContent = 'Tong so tu: 0';
    
    const storyContainer = document.createElement('div');
    output.appendChild(storyContainer);
    
    try {
        const response = await fetch(`${API_URL}/generate-story`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                refined_prompt: globalData.refinedPrompt,
                story_length: globalData.selectedLength
            })
        });
        
        if (!response.ok) {
            throw new Error(`Loi server: ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let fullStory = "";
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            fullStory += chunk;
            
            // Format story with paragraphs
            const formattedStory = fullStory
                .split('\n')
                .filter(line => line.trim())
                .map(line => `<p>${line}</p>`)
                .join('');
            
            storyContainer.innerHTML = formattedStory;
            
            // Update word count
            const wordCount = fullStory.trim().split(/\s+/).filter(word => word.length > 0).length;
            wordCountDisplay.textContent = `Tong so tu: ${wordCount}`;
            
            // Auto scroll to bottom of the output container
            output.scrollTop = output.scrollHeight;
        }
    } catch (error) {
        output.innerHTML += `<p style="color: red;">Loi: ${error.message}</p>`;
    }
}

// Download story as .txt
function downloadStory() {
    const storyText = document.getElementById('storyOutput').innerText;
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(storyText));
    element.setAttribute('download', 'truyen.txt');
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
}

// Reset form
function resetForm() {
    globalData = {
        initialPrompt: "",
        userAnswers: [],
        refinedPrompt: "",
        selectedLength: "medium"
    };
    document.getElementById('initialPrompt').value = '';
    
    // Clear selections
    selectedTags.clear();
    selectedThemes.clear();
    document.querySelectorAll('.selected-tag').forEach(el => el.classList.remove('selected-tag'));
    
    showPhase(1);
}

// Fetch trending topics on load
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
            if (selectedTags.has(genre)) {
                selectedTags.delete(genre);
            } else {
                selectedTags.add(genre);
            }
        };
        genresContainer.appendChild(tag);
    });
}

async function fetchTrendingTopics() {
    try {
        const response = await fetch(`${API_URL}/trending-topics`);
        const data = await response.json();
        if (data.status === 'success') {
            const trendingContainer = document.getElementById('trendingContainer');
            if (!trendingContainer) return;
            trendingContainer.innerHTML = '';
            
            data.topics.forEach(topic => {
                const tag = document.createElement('div');
                tag.className = 'trending-tag';
                tag.textContent = topic.title;
                tag.title = topic.description;
                tag.onclick = (e) => {
                    e.preventDefault();
                    tag.classList.toggle('selected-tag');
                    if (selectedThemes.has(topic.title)) {
                        selectedThemes.delete(topic.title);
                    } else {
                        selectedThemes.add(topic.title);
                    }
                };
                trendingContainer.appendChild(tag);
            });
        }
    } catch (error) {
        console.error('Loi tai trending topics:', error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initGenres();
    fetchTrendingTopics();
});

// Lịch sử truyện (History)
async function openHistory() {
    document.getElementById('historyModal').style.display = 'block';
    const list = document.getElementById('historyList');
    list.innerHTML = 'Đang tải...';
    try {
        const res = await fetch(`${API_URL}/stories`);
        const data = await res.json();
        if(data.status === 'success') {
            if(data.stories.length === 0) {
                list.innerHTML = '<p style="text-align:center; color:#777; margin-top:20px;">Bạn chưa tạo truyện nào.</p>';
                return;
            }
            list.innerHTML = '';
            data.stories.forEach(s => {
                const item = document.createElement('div');
                item.className = 'history-item';
                item.innerHTML = `
                    <div class="history-title">${s.title}</div>
                    <div class="history-meta">⏳ ${s.created_at} | 📝 ${s.word_count} từ</div>
                    <div class="history-snippet">${s.snippet}</div>
                `;
                item.onclick = () => loadStory(s.id);
                list.appendChild(item);
            });
        }
    } catch(e) {
        list.innerHTML = '<p style="color:red;">Lỗi tải lịch sử truyện.</p>';
    }
}

function closeHistory() {
    document.getElementById('historyModal').style.display = 'none';
}

async function loadStory(id) {
    closeHistory();
    showPhase(4);
    const output = document.getElementById('storyOutput');
    output.innerHTML = '<div class="loading"><div class="spinner"></div><p>Đang tải truyện...</p></div>';
    try {
        const res = await fetch(`${API_URL}/stories/${id}`);
        const data = await res.json();
        if(data.status === 'success') {
            const formattedStory = data.story.story_content
                .split('\n')
                .filter(line => line.trim())
                .map(line => `<p>${line}</p>`)
                .join('');
            output.innerHTML = `<div>${formattedStory}</div>`;
            document.getElementById('wordCount').textContent = `Tổng số từ: ${data.story.word_count}`;
        }
    } catch(e) {
        output.innerHTML = '<p style="color:red;">Lỗi tải truyện.</p>';
    }
}

// Đóng modal khi click ra ngoài
window.onclick = function(event) {
    const modal = document.getElementById('historyModal');
    if (event.target == modal) {
        closeHistory();
    }
}

// Sao chép
function copyStory() {
    const storyText = document.getElementById('storyOutput').innerText;
    navigator.clipboard.writeText(storyText).then(() => {
        alert('Đã sao chép truyện vào bộ nhớ tạm!');
    }).catch(err => {
        console.error('Lỗi sao chép: ', err);
    });
}
