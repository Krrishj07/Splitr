document.addEventListener('DOMContentLoaded', () => {

    // Selecting HTML element
    const form = document.getElementById('expense-form');
    const splitMethodRadios = document.querySelectorAll('input[name="split-method"]');
    const percentageInputs = document.getElementById('percentage-inputs');
    const amountInputs = document.getElementById('amount-inputs');
    const resultsSection = document.getElementById('results-section');
    const balancesSection = document.getElementById('balances-section');
    
    // Core Funtions

    // Function to show/hide dynamic input fields
    function updateVisibleInputs() {
        const selectedMethod = document.querySelector('input[name="split-method"]:checked').value;
        percentageInputs.classList.add('hidden');
        amountInputs.classList.add('hidden');
        if (selectedMethod === 'percentage') percentageInputs.classList.remove('hidden');
        if (selectedMethod === 'amount') amountInputs.classList.remove('hidden');
    }

    // Function to update the final balances display
    function updateFinalBalances(balances) {
        let summaryHTML = `<h2>Final Totals:</h2>`;
        const balanceA = balances['Person A'];
        let finalSummary = '';

        if (Math.abs(balanceA) < 0.01) {
            finalSummary = '<p>No data to show.</p>';
        } else if (balanceA > 0) {
            finalSummary = `<p><strong>Overall:</strong> Person B owes Person A <span class="owed-money">$${balanceA.toFixed(2)}</span>.</p>`;
        } else {
            finalSummary = `<p><strong>Overall:</strong> Person A owes Person B <span class="owes-money">$${Math.abs(balanceA).toFixed(2)}</span>.</p>`;
        }
        balancesSection.innerHTML = summaryHTML + finalSummary;
    }

    // Dependent Functions
    
    // checking for radio button changes
    splitMethodRadios.forEach(radio => radio.addEventListener('change', updateVisibleInputs));

    // checking for the main form submission
    form.addEventListener('submit', (event) => {
        event.preventDefault();

        // Balances are reset for every new calculation
        const balances = { 'Person A': 0, 'Person B': 0 };

        const totalAmount = parseFloat(document.getElementById('total-amount').value);
        const payer = document.getElementById('payer').value;
        const splitMethod = document.querySelector('input[name="split-method"]:checked').value;

        // Validation
        if (isNaN(totalAmount) || totalAmount <= 0) {
            resultsSection.innerHTML = `<p style="color: red;">Please enter a valid total amount.</p>`;
            return;
        }
        if (!payer) {
            resultsSection.innerHTML = `<p style="color: red;">Please select who paid.</p>`;
            return;
        }

        let personAShare = 0;
        let personBShare = 0;

        // Calculation logic
        switch (splitMethod) {
            case 'equally':
                personAShare = totalAmount / 2;
                personBShare = totalAmount / 2;
                break;
            case 'percentage':
                const percentA = parseFloat(document.getElementById('person-a-percentage').value) || 0;
                const percentB = parseFloat(document.getElementById('person-b-percentage').value) || 0;
                if (percentA + percentB !== 100) {
                    resultsSection.innerHTML = `<p style="color: red;">Error: Percentages must add up to 100.</p>`;
                    return;
                }
                personAShare = (percentA / 100) * totalAmount;
                personBShare = (percentB / 100) * totalAmount;
                break;
            case 'amount':
                const amountA = parseFloat(document.getElementById('person-a-amount').value) || 0;
                const amountB = parseFloat(document.getElementById('person-b-amount').value) || 0;
                if (amountA > totalAmount || amountB > totalAmount) {
                    resultsSection.innerHTML = `<p style="color: red;">Error: A person's share cannot be more than the total amount.</p>`;
                    return;
                }
                if (Math.abs(amountA + amountB - totalAmount) > 0.001) {
                    resultsSection.innerHTML = `<p style="color: red;">Error: Exact amounts must add up to the total of $${totalAmount.toFixed(2)}.</p>`;
                    return;
                }
                personAShare = amountA;
                personBShare = amountB;
                break;
        }

        // Update balances for this single transaction
        if (payer === 'Person A') balances['Person A'] += totalAmount;
        else if (payer === 'Person B') balances['Person B'] += totalAmount;
        balances['Person A'] -= personAShare;
        balances['Person B'] -= personBShare;

        // Display results
        const description = document.getElementById('description').value || 'This expense';
        resultsSection.innerHTML = `<p>For "${description}", Person A's share is $${personAShare.toFixed(2)} and Person B's share is $${personBShare.toFixed(2)}.</p>`;
        
        // Update the final totals display with the result of this single calculation
        updateFinalBalances(balances);
    });

    // Initalize
    updateVisibleInputs();
});