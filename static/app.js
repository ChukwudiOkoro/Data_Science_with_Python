const expressionEl = document.getElementById('expression');
const resultEl = document.getElementById('result');
const clearBtn = document.getElementById('clear');
const calculateBtn = document.getElementById('calculate');
const buttons = document.querySelectorAll('[data-value]');

let expression = '';

function updateDisplay() {
  expressionEl.textContent = expression || 'Enter expression';
}

function showResult(value) {
  resultEl.textContent = value;
}

function appendValue(value) {
  if (value === ',') {
    expression += ',';
  } else if (value === '^') {
    expression += '**';
  } else {
    expression += value;
  }
  updateDisplay();
}

async function calculateExpression() {
  if (!expression.trim()) {
    return;
  }

  try {
    const response = await fetch('/api/calc', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ expression }),
    });
    const data = await response.json();

    if (data.error) {
      showResult(data.error);
    } else {
      showResult(data.result);
    }
  } catch (error) {
    showResult('Network error');
  }
}

buttons.forEach((button) => {
  button.addEventListener('click', () => appendValue(button.dataset.value));
});

calculateBtn.addEventListener('click', calculateExpression);
clearBtn.addEventListener('click', () => {
  expression = '';
  updateDisplay();
  showResult('0');
});

window.addEventListener('keydown', (event) => {
  const key = event.key;
  const allowed = '0123456789.+-*/()%,';

  if (allowed.includes(key)) {
    appendValue(key);
    return;
  }

  if (key === 'Enter') {
    calculateExpression();
  }

  if (key === 'Backspace') {
    expression = expression.slice(0, -1);
    updateDisplay();
  }
});

updateDisplay();
