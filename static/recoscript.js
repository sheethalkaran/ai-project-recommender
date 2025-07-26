let currentIndex = 10;
const loadMoreBtn = document.getElementById('load-more');
const container = document.getElementById('project-container');

function attachLevelButtonLogic(cardElement) {
  const buttons = cardElement.querySelectorAll('button');
  buttons.forEach(btn => {
    btn.classList.add('level-btn');
    btn.setAttribute('data-project', cardElement.querySelector('h3')?.innerText);
    btn.setAttribute('data-level', btn.innerText);
    const matchingSkills = cardElement.querySelector('span.text-green-600')?.innerText.split(', ') || [];
    const missingSkills = cardElement.querySelector('span.text-red-600')?.innerText.split(', ') || [];
    btn.setAttribute('data-matching', JSON.stringify(matchingSkills));
    btn.setAttribute('data-missing', JSON.stringify(missingSkills));
  });
}

document.querySelectorAll('#project-container > div').forEach(attachLevelButtonLogic);

loadMoreBtn?.addEventListener('click', () => {
  const nextProjects = allProjects.slice(currentIndex, currentIndex + 10);

  nextProjects.forEach(project => {
    const div = document.createElement('div');
    div.className = "relative bg-white bg-opacity-90 shadow-md rounded-xl p-6 border-l-4 border-indigo-500 transition-transform hover:scale-[1.02] group flex justify-between items-start";

    div.innerHTML = `
      <div class="w-3/4 pr-4">
        <h3 class="text-2xl font-bold text-indigo-700">${project.project_name}</h3>
        <p class="mt-2 text-gray-700 text-base">
          <strong>Matching Skills Count:</strong> ${project.matching_count}
        </p>
        <p class="text-gray-700">
          <strong>Matching Skills:</strong>
          <span class="text-green-600">${project.matching_skills.join(', ')}</span>
        </p>
        <p class="text-gray-700">
          <strong>Missing Skills:</strong>
          <span class="text-red-600">${project.missing_skills.join(', ') || 'None'}</span>
        </p>
      </div>

      <div class="w-1/4 opacity-0 group-hover:opacity-100 transition-opacity duration-300 ease-in-out space-y-2">
        <p class="text-sm text-gray-500 font-semibold">Select Level:</p>
        <button class="w-full px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 font-bold">Beginner</button>
        <button class="w-full px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 font-bold">Intermediate</button>
        <button class="w-full px-2 py-1 text-xs bg-pink-100 text-pink-700 rounded hover:bg-pink-200 font-bold">Advanced</button>
      </div>
    `;

    container.appendChild(div);
    attachLevelButtonLogic(div);
  });

  currentIndex += 10;
  if (currentIndex >= allProjects.length) {
    loadMoreBtn.style.display = 'none';
  }
});

// Chatbot modal behavior
let chatMessages = [];
const inputField = document.getElementById('chatbot-input');
const chatContent = document.getElementById('chatbot-content');
const chatbot = document.getElementById('chatbot-modal');
const toggleSizeBtn = document.getElementById('toggle-size');
let isMaximized = false;

toggleSizeBtn.addEventListener('click', () => {
  isMaximized = !isMaximized;
  if (isMaximized) {
    chatbot.classList.remove('w-[350px]', 'h-[550px]', 'rounded-xl', 'bottom-4', 'right-4');
    chatbot.classList.add('w-[80vw]', 'h-[92vh]', 'rounded-lg', 'bottom-4', 'right-4');
    toggleSizeBtn.textContent = '🗗';
  } else {
    chatbot.classList.remove('w-[80vw]', 'h-[92vh]', 'rounded-lg', 'bottom-4', 'right-4');
    chatbot.classList.add('w-[350px]', 'h-[550px]', 'rounded-xl', 'bottom-4', 'right-4');
    toggleSizeBtn.textContent = '🗖';
  }
});


// Chat send
inputField.addEventListener("keypress", function (e) {
  if (e.key === "Enter") {
    const input = e.target.value.trim();
    if (!input) return;
    appendMessage("user", input);
    sendToAIChat(input);
    e.target.value = '';
  }
});

function sendToAIChat(userMessage) {
  chatMessages.push({ role: "user", content: userMessage });
  appendMessage("assistant", "Bot is typing...");
  const typingElem = document.querySelector('#chatbot-content > .flex:last-child');

  fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages: chatMessages })
  })
    .then(res => res.json())
    .then(data => {
      if (typingElem) typingElem.remove();
      chatMessages.push({ role: "assistant", content: data.reply });
      appendMessage("assistant", data.reply);
    })
    .catch(err => {
      console.error('Error in chat:', err);
      if (typingElem) typingElem.remove();
      appendMessage("assistant", "Oops! Something went wrong.");
    });
}

function appendMessage(role, content) {
  const chat = document.getElementById('chatbot-content');
  const msgWrapper = document.createElement('div');
  msgWrapper.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'} w-full`;


const bubble = document.createElement('div');
bubble.className = `max-w-[75%] px-5 py-3 rounded-2xl shadow text-lg font-[Roboto] leading-relaxed tracking-wide transition-opacity duration-300 ease-in opacity-0 animate-fadeIn ${
  role === 'user'
    ? 'bg-gray-700 text-white rounded-bl-none'    // dark grey background for user
    : 'bg-blue-900 text-white rounded-br-none'    // dark blue background for bot
}`;




  bubble.innerText = content;

  const time = document.createElement('div');
  time.className = 'text-[10px] text-gray-400 mt-1 text-right';
  time.innerText = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  bubble.appendChild(time);

  msgWrapper.appendChild(bubble);
  chat.appendChild(msgWrapper);
  chat.scrollTop = chat.scrollHeight;
}

function handleSend(event) {
  if (event) event.preventDefault();  // Prevent default form submit if called by a button
  const input = document.getElementById('chatbot-input');
  const message = input.value.trim();
  if (message) {
    console.log("User sent:", message);
    input.value = '';
  }
}


function showChatbotWithProject(button) {
  const project = button.getAttribute('data-project');
  const level = button.getAttribute('data-level');
  const matching = JSON.parse(button.getAttribute('data-matching'));
  const missing = JSON.parse(button.getAttribute('data-missing'));

  const firstPrompt = `Project: ${project}\nLevel: ${level}\nMatching Skills: ${matching.join(', ')}\nMissing Skills: ${missing.join(', ')}\nGive a detailed project description.`;

  chatMessages = [{ role: "user", content: firstPrompt }];
  document.getElementById('chatbot-project-title').innerText = project;
  document.getElementById('chatbot-level-info').innerText = `Level: ${level}`;
  document.getElementById('chatbot-modal').classList.remove('hidden');

  sendToAIChat(firstPrompt);
}

document.addEventListener('click', function (e) {
  if (e.target.classList.contains('level-btn')) {
    showChatbotWithProject(e.target);
  }
});

function closeChatbot() {
  document.getElementById('chatbot-modal').classList.add('hidden');
}
