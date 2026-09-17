document.addEventListener("DOMContentLoaded", function () {
  const btnOpen = document.getElementById("condor-img"); // Usar la imagen de la mascota
  const btnClose = document.getElementById("condy-chat-close");
  const window = document.getElementById("condy-chat-window");
  const messagesContainer = document.getElementById("condy-chat-messages");
  const input = document.getElementById("condy-chat-input-text");
  const btnSend = document.getElementById("condy-chat-send");
  const optionsContainer = document.getElementById("condy-chat-options");
  const bubble = document.getElementById('condor-speech-bubble');
  
  let isFirstOpen = true;

  // Opciones iniciales frecuentes (CA2)
  const initialOptions = [
    "¿Cuáles son sus horarios?",
    "¿Dónde están ubicados?",
    "¿Qué servicios ofrecen?"
  ];

  // Restaurar historial del sessionStorage
  let chatHistory = JSON.parse(sessionStorage.getItem('condy_chat_history') || '[]');
  
  if (chatHistory.length > 0) {
      isFirstOpen = false;
      // Recrear mensajes
      chatHistory.forEach(msg => {
          if (msg.type === 'message') {
              addMessage(msg.text, msg.sender, false);
          } else if (msg.type === 'options') {
              showOptions(msg.options, false);
          } else if (msg.type === 'fallback') {
              showFallbackOption(false);
          }
      });
  }

  // Alternar ventana de chat
  if (btnOpen) {
      btnOpen.addEventListener("click", (e) => {
          e.stopPropagation();
          const mascotContainer = document.getElementById('condor-mascot-container');
          if (mascotContainer && mascotContainer.classList.contains('collapsed')) {
              return;
          }
          toggleChat();
      });
  }
  
  if (btnClose) {
      btnClose.addEventListener("click", (e) => {
          e.stopPropagation();
          toggleChat(false);
      });
  }

  function toggleChat(forceState = null) {
    const isHidden = window.classList.contains("d-none");
    const willShow = forceState !== null ? forceState : isHidden;
    
    if (willShow) {
      window.classList.remove("d-none");
      
      if (isFirstOpen) {
        const greeting = "¡Hola! Soy Condy, tu asistente virtual. ¿En qué puedo ayudarte hoy?";
        addMessage(greeting, "bot");
        showOptions(initialOptions);
        isFirstOpen = false;
      }
      setTimeout(() => input.focus(), 300);
    } else {
      window.classList.add("d-none");
    }
  }

  // Manejar input de texto
  input.addEventListener("input", function() {
    btnSend.disabled = this.value.trim().length === 0;
  });

  input.addEventListener("keypress", function(e) {
    if (e.key === "Enter" && !btnSend.disabled) {
      handleSend();
    }
  });

  btnSend.addEventListener("click", handleSend);

  function saveToHistory(item) {
      chatHistory.push(item);
      sessionStorage.setItem('condy_chat_history', JSON.stringify(chatHistory));
  }

  function handleSend() {
    const text = input.value.trim();
    if (!text) return;
    
    input.value = "";
    btnSend.disabled = true;
    hideOptions();
    
    addMessage(text, "user");
    showTypingIndicator();
    
    // Llamada al backend
    fetch('/api/chat/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') // Obtener token CSRF
      },
      body: JSON.stringify({ message: text })
    })
    .then(response => response.json())
    .then(data => {
      removeTypingIndicator();
      if (data.response) {
        addMessage(data.response, "bot");
      }
      if (data.options && data.options.length > 0) {
        showOptions(data.options);
      }
      if (data.fallback_action === 'ticket') {
        showFallbackOption();
      }
    })
    .catch(error => {
      removeTypingIndicator();
      console.error('Error:', error);
      addMessage("Lo siento, hubo un problema de conexión. Intenta de nuevo más tarde.", "bot");
    });
  }

  function addMessage(text, sender, save = true) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender}`;
    // Convertir saltos de línea a <br>
    bubble.innerHTML = text.replace(/\\n/g, '<br>');
    messagesContainer.appendChild(bubble);
    scrollToBottom();
    
    if (save) {
        saveToHistory({ type: 'message', text: text, sender: sender });
    }
  }

  function showOptions(options, save = true) {
    optionsContainer.innerHTML = '';
    options.forEach(opt => {
      const btn = document.createElement('button');
      btn.className = 'chat-option-btn';
      btn.innerText = opt;
      btn.addEventListener('click', () => {
        input.value = opt;
        btnSend.disabled = false;
        handleSend();
      });
      optionsContainer.appendChild(btn);
    });
    optionsContainer.classList.remove('d-none');
    optionsContainer.classList.add('d-flex');
    scrollToBottom();
    
    if (save) {
        saveToHistory({ type: 'options', options: options });
    }
  }

  function hideOptions() {
    optionsContainer.classList.add('d-none');
    optionsContainer.classList.remove('d-flex');
  }

  function showTypingIndicator() {
    const typing = document.createElement('div');
    typing.id = 'condy-typing';
    typing.className = 'condy-typing-indicator';
    typing.innerHTML = '<div class="condy-typing-dot"></div><div class="condy-typing-dot"></div><div class="condy-typing-dot"></div>';
    messagesContainer.appendChild(typing);
    scrollToBottom();
  }

  function removeTypingIndicator() {
    const typing = document.getElementById('condy-typing');
    if (typing) {
      typing.remove();
    }
  }

  function showFallbackOption(save = true) {
    const div = document.createElement('div');
    div.className = 'mt-2 mb-2 d-flex justify-content-start';
    div.innerHTML = `<a href="/contactanos/" class="btn btn-sm btn-outline-primary rounded-pill" style="border-color:#198754; color:#198754;">Dejar un Ticket / Contactar Soporte</a>`;
    messagesContainer.appendChild(div);
    scrollToBottom();
    
    if (save) {
        saveToHistory({ type: 'fallback' });
    }
  }

  function scrollToBottom() {
    setTimeout(() => {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }, 50);
  }

  // Función auxiliar para CSRF Token en Django
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
});
