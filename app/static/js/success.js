document.addEventListener('DOMContentLoaded', () => {
    const copyButton = document.getElementById('copyButton');
    if (copyButton) {
      copyButton.addEventListener('click', copyLink);
    }
  });
  
  function copyLink() {
    const copyText = document.getElementById("downloadLink");
    if (!copyText || !copyText.value) {
      alert("Ошибка: ссылка отсутствует!");
      return;
    }
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
      // Попытка использовать Clipboard API
      navigator.clipboard.writeText(copyText.value)
        .then(() => {
          alert("Ссылка скопирована в буфер обмена!");
        })
        .catch(err => {
          console.error("Ошибка копирования с Clipboard API: ", err);
          fallbackCopyText(copyText);
        });
    } else {
      // Если Clipboard API не поддерживается, используем fallback
      fallbackCopyText(copyText);
    }
  }
  
  function fallbackCopyText(copyText) {
    // Создаем временный textarea, если необходимо
    // Если copyText уже является input, можно просто его выделить
    copyText.select();
    try {
      const successful = document.execCommand('copy');
      if (successful) {
        alert("Ссылка скопирована в буфер обмена!");
      } else {
        alert("Не удалось скопировать ссылку!");
      }
    } catch (err) {
      console.error("Fallback: Ошибка копирования: ", err);
      alert("Не удалось скопировать ссылку!");
    }
  }

  
  
  
  