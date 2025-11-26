document.getElementById('triageForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    // 1. Collect Data
    const data = {
        age: document.getElementById('age').value,
        gender: document.getElementById('gender').value,
        complaint: document.getElementById('complaint').value,
        esi: parseFloat(document.getElementById('esi').value),
        vitals: document.getElementById('vitals').value,
        background: document.getElementById('background').value,
        remarks: document.getElementById('remarks').value
    };

    // 2. Show Loader
    const btn = document.getElementById('submitBtn');
    const btnText = btn.querySelector('.btn-text');
    const loader = btn.querySelector('.loader');

    btn.disabled = true;
    btnText.classList.add('hidden');
    loader.classList.remove('hidden');

    // Hide previous results
    document.getElementById('resultsSection').classList.add('hidden');

    try {
        // 3. Call API
        const response = await fetch('/triage', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error('API Error');
        }

        const result = await response.json();

        // 4. Update UI
        updateUI(result);

    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred during triage analysis. Please try again.');
    } finally {
        // Reset Button
        btn.disabled = false;
        btnText.classList.remove('hidden');
        loader.classList.add('hidden');
    }
});

function updateUI(result) {
    const resultsSection = document.getElementById('resultsSection');
    resultsSection.classList.remove('hidden');

    // --- Final Decision ---
    const decisionBadge = document.getElementById('decisionBadge');
    const decisionReason = document.getElementById('decisionReason');
    const decisionSource = document.getElementById('decisionSource');
    const finalCard = document.getElementById('finalDecisionCard');

    decisionBadge.textContent = result.final_decision.toUpperCase();
    decisionReason.textContent = result.reason;
    decisionSource.textContent = result.source;

    // Style based on decision
    if (result.final_decision.toLowerCase() === 'admit') {
        decisionBadge.className = 'decision-badge badge-admit';
        finalCard.style.borderLeftColor = '#EF4444'; // Red
    } else {
        decisionBadge.className = 'decision-badge badge-discharge';
        finalCard.style.borderLeftColor = '#10B981'; // Green
    }

    // --- Agent Votes ---
    updateAgentCard('safety', result.votes.safety);
    updateAgentCard('pathology', result.votes.pathology);
    updateAgentCard('discharge', result.votes.discharge);
    updateAgentCard('geriatric', result.votes.geriatric);
}

function updateAgentCard(agentId, voteData) {
    const voteEl = document.getElementById(`${agentId}Vote`);
    const reasonEl = document.getElementById(`${agentId}Reason`);

    // Normalize decision string
    let decision = voteData.decision || "Uncertain";
    if (decision.toLowerCase().includes('admit')) decision = 'ADMIT';
    else if (decision.toLowerCase().includes('discharge')) decision = 'DISCHARGE';

    voteEl.textContent = decision;
    reasonEl.textContent = voteData.reason;

    // Style
    if (decision === 'ADMIT') {
        voteEl.className = 'agent-vote vote-admit';
    } else {
        voteEl.className = 'agent-vote vote-discharge';
    }
}
