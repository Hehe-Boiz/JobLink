export const validateForm = (jobData) => {
    let errors = []; 


    if (!jobData.title.trim()) errors.push("- Tiêu đề công việc không được để trống.");
    if (!jobData.address.trim()) errors.push("- Địa chỉ chi tiết không được để trống.");
    if (!jobData.description.trim()) errors.push("- Mô tả công việc không được để trống.");
    if (!jobData.requirements.trim()) errors.push("- Yêu cầu ứng viên không được để trống.");
    if (!jobData.benefits.trim()) errors.push("- Quyền lợi không được để trống.");

    const minSalary = parseInt(jobData.salaryMin);
    const maxSalary = parseInt(jobData.salaryMax);
    const hasMin = !isNaN(minSalary);
    const hasMax = !isNaN(maxSalary);

    if (jobData.salaryMin && !hasMin) errors.push("- Lương tối thiểu phải là số.");
    if (jobData.salaryMax && !hasMax) errors.push("- Lương tối đa phải là số.");

    if (hasMin && minSalary < 0) errors.push("- Lương tối thiểu không được âm.");
    if (hasMax && maxSalary < 0) errors.push("- Lương tối đa không được âm.");

    if (hasMin && hasMax && minSalary > maxSalary) {
        errors.push("- Lương tối thiểu không được lớn hơn lương tối đa.");
    }

    if (jobData.deadline) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        if (jobData.deadline < today) {
            errors.push("- Hạn nộp hồ sơ phải là ngày trong tương lai.");
        }
    } else {
        errors.push("- Chưa chọn hạn nộp hồ sơ.");
    }

    if (errors.length > 0) {
        console.log("Errors:", errors)
        return [false, errors];
    }

    return [true, null];
};
