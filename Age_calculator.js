document.getElementById('ageForm').addEventListener('submit', function(event) {
    event.preventDefault();

    const day = parseInt(document.getElementById('day').value, 10);
    const month = parseInt(document.getElementById('month').value, 10);
    const year = parseInt(document.getElementById('year').value, 10);
    const resultDiv = document.getElementById('ageResult');

    // Validate date
    const dob = new Date(year, month - 1, day);
    if (
        dob.getFullYear() !== year ||
        dob.getMonth() !== month - 1 ||
        dob.getDate() !== day
    ) {
        resultDiv.textContent = 'Invalid date. Please enter a valid date of birth.';
        resultDiv.style.color = 'red';
        return;
    }

    const today = new Date();
    let ageYears = today.getFullYear() - year;
    let ageMonths = today.getMonth() - (month - 1);
    let ageDays = today.getDate() - day;

    if (ageDays < 0) {
        ageMonths--;
        const lastMonth = new Date(today.getFullYear(), today.getMonth(), 0);
        ageDays += lastMonth.getDate();
    }
    if (ageMonths < 0) {
        ageYears--;
        ageMonths += 12;
    }

    if (ageYears < 0) {
        resultDiv.textContent = 'Date of birth is in the future!';
        resultDiv.style.color = 'red';
        return;
    }

    resultDiv.textContent = `You are ${ageYears} year${ageYears !== 1 ? 's' : ''}, ${ageMonths} month${ageMonths !== 1 ? 's' : ''}, and ${ageDays} day${ageDays !== 1 ? 's' : ''} old.`;
    resultDiv.style.color = '#2d7a2d';
}); 
