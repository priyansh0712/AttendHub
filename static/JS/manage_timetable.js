document.addEventListener('DOMContentLoaded', function() {
    loadTimetable();

    // Logout Logic
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async function() {
            try {
                await apiPostJson('/api/auth/logout', {});
                window.location.href = '/admin/login';
            } catch (error) {
                console.error('Logout error:', error);
                window.location.href = '/admin/login'; 
            }
        });
    }

    // Upload Timetable
    const uploadBtn = document.getElementById('uploadBtn');
    if (uploadBtn) {
        uploadBtn.addEventListener('click', async function() {
            const fileInput = document.getElementById('timetableInput');
            const errorDiv = document.getElementById('uploadError');
            errorDiv.style.display = 'none';
            errorDiv.textContent = '';

            if (fileInput.files.length === 0) {
                errorDiv.textContent = 'Please select a CSV file first.';
                errorDiv.style.display = 'block';
                return;
            }

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            const originalText = uploadBtn.innerHTML;
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Uploading...';

            try {
                const result = await apiPostForm('/api/admin/timetable/upload', formData);

                const successCount = result && typeof result.success_count === 'number' ? result.success_count : 0;
                const errors = result && Array.isArray(result.errors) ? result.errors : [];

                if (errors.length > 0) {
                    errorDiv.innerHTML = `Imported ${successCount} rows. ${errors.length} error(s):<br>` +
                        errors.slice(0, 6).map(e => `• ${e}`).join('<br>') +
                        (errors.length > 6 ? '<br>• ...' : '');
                    errorDiv.style.display = 'block';
                }

                if (successCount > 0) {
                    alert(`Timetable imported: ${successCount} row(s).`);
                    fileInput.value = '';
                    loadTimetable();
                }
            } catch (error) {
                console.error('Error:', error);
                errorDiv.textContent = getApiErrorMessage(error, 'Upload failed.');
                errorDiv.style.display = 'block';
            } finally {
                uploadBtn.disabled = false;
                uploadBtn.innerHTML = originalText;
            }
        });
    }
});

async function loadTimetable() {
    try {
        const timetableData = await apiGet('/api/admin/timetable/list');
            const tbody = document.getElementById('timetableTableBody');
            tbody.innerHTML = ''; 

            if (timetableData.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">No schedule available. Upload a CSV to get started.</td></tr>';
                return;
            }

            timetableData.forEach(item => {
                const row = document.createElement('tr');
                // Format time: 09:00:00 -> 09:00
                const startTime = item.start_time ? item.start_time.substring(0, 5) : '';
                const endTime = item.end_time ? item.end_time.substring(0, 5) : '';

                row.innerHTML = `
                    <td class="ps-4 text-start fw-bold text-muted">${item.department || '-'}</td>
                    <td>${item.semester ? item.semester + 'th Sem' : '-'}</td>
                    <td>${item.day}</td>
                    <td>${startTime} - ${endTime}</td>
                    <td>
                        <div class="fw-bold">${item.subject}</div>
                        <div class="small text-muted">${item.faculty_name}</div>
                    </td>
                    <td class="text-end pe-4"><span class="badge bg-success">Scheduled</span></td>
                `;
                tbody.appendChild(row);
            });
    } catch (error) {
        console.error('Failed to load timetable:', error);
        const tbody = document.getElementById('timetableTableBody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-danger">Failed to load schedule. Please refresh.</td></tr>';
        }
    }
}
