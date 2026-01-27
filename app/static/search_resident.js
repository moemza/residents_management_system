document.addEventListener('DOMContentLoaded', function() {
    var searchType = document.getElementById('search_type');
    var nameGroup = document.getElementById('name_query_group');
    var residentGroup = document.getElementById('resident_query_group');
    var qualificationGroup = document.getElementById('qualification_query_group');
    var skillGroup = document.getElementById('skill_query_group');

    function toggleSearchInput() {
        nameGroup.style.display = 'none';
        residentGroup.style.display = 'none';
        qualificationGroup.style.display = 'none';
        skillGroup.style.display = 'none';

        if (searchType.value === 'name') {
            nameGroup.style.display = 'block';
        } else if (searchType.value === 'resident') {
            residentGroup.style.display = 'block';
        } else if (searchType.value === 'qualification') {
            qualificationGroup.style.display = 'block';
        } else if (searchType.value === 'skill') {
            skillGroup.style.display = 'block';
        }
    }

    searchType.addEventListener('change', toggleSearchInput);
    toggleSearchInput(); // Initialize on page load
});