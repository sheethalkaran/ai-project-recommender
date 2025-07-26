document.getElementById('skills-dropdown').addEventListener('change', function () {
    const selectedSkill = this.value;
    const skillsInput = document.getElementById('skills');
    const selectedSkillsDiv = document.getElementById('selected-skills');

    let currentSkills = skillsInput.value.trim();
    let skillsArray = currentSkills ? currentSkills.split(',').map(skill => skill.trim()) : [];

    if (selectedSkill && !skillsArray.includes(selectedSkill)) {
        skillsArray.push(selectedSkill);
        skillsInput.value = skillsArray.join(', ');
        selectedSkillsDiv.textContent = "Skills: " + skillsArray.join(', ');
    }

    this.selectedIndex = [...this.options].findIndex(opt => opt.disabled);
});

document.getElementById('resumeUpload').addEventListener('change', function () {
    const fileName = this.files[0]?.name || '';
    document.getElementById('selected-resume').textContent = fileName ? "Selected file: " + fileName : '';
});

document.getElementById('skillsForm').addEventListener('submit', function (event) {


    const skillsInput = document.getElementById('skills').value;
    const skills = skillsInput.split(',').map(skill => skill.trim()).filter(skill => skill);

    if (skills.length === 0) {
        alert("Please enter at least one skill.");
        return;
    }

  fetch('/submit_skills', {

        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skills })
    })
    .then(response => response.json())
    .then(data => {
        const resultsDiv = document.getElementById('results');
        const top6Div = document.getElementById('top6');
        resultsDiv.innerHTML = '';
        top6Div.innerHTML = '';

        if (data.recommended_projects && data.top_6_projects) {
            const recommendations = data.recommended_projects;
            const top6 = data.top_6_projects;

            let recHTML = '<h2 class="text-2xl font-bold text-indigo-600 mb-4">Recommended Projects</h2>';
            recHTML += '<ul class="list-disc pl-5 space-y-1">';
            recommendations.forEach(project => {
                recHTML += `<li>${project}</li>`;
            });
            recHTML += '</ul>';
            resultsDiv.innerHTML = recHTML;

            let top6HTML = '<h2 class="text-2xl font-bold text-purple-600 mb-4 mt-8">Top 6 Project Matches</h2>';
            top6.forEach(item => {
                top6HTML += `
                    <div class="mb-4 p-4 rounded-lg bg-white bg-opacity-80 shadow-md">
                        <h3 class="text-lg font-semibold text-indigo-700">${item.project}</h3>
                        <p class="text-sm text-gray-700 mt-1">
                            <strong>Matching Skills (${item.matching_count}):</strong> ${item.matching_skills.join(', ')}
                        </p>
                        <p class="text-sm text-gray-600">
                            <strong>Missing Skills:</strong> ${item.missing_skills.length > 0 ? item.missing_skills.join(', ') : 'None'}
                        </p>
                    </div>
                `;
            });
            top6Div.innerHTML = top6HTML;

        } else {
            resultsDiv.innerHTML = `<p class="text-red-500 font-semibold">No projects found for the entered skills.</p>`;
        }
    })
});

document.getElementById('load-more').addEventListener('click', function () {
    currentPage++;
    fetchProjects(currentSkills, currentPage);
});


function toggleForm(formType) {
    const skillsForm = document.getElementById('skillsForm');
    const resumeForm = document.getElementById('resume-form');
    const enterSkillsBtn = document.getElementById('enter-skills-btn');
    const uploadResumeBtn = document.getElementById('upload-resume-btn');

    if (formType === 'skills') {
        skillsForm.parentElement.style.display = 'block';
        resumeForm.parentElement.style.display = 'none';
        enterSkillsBtn?.classList.add('active');
        uploadResumeBtn?.classList.remove('active');
    } else {
        skillsForm.parentElement.style.display = 'none';
        resumeForm.parentElement.style.display = 'block';
        uploadResumeBtn?.classList.add('active');
        enterSkillsBtn?.classList.remove('active');
    }
}
